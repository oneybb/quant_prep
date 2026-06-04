
# Global para
exchange_latency_ms = 20
maker_fee_bps = -1
max_abs_position = 1.5
stale_threshold_bps = 3
post_fill_horizon_ms = 200


class Order:
    def __init__ (self, status, order_id, side, price, size):
        ''' PENDING_NEW
                LIVE
                PENDING_CANCEL
                CANCELLED
                PARTIALLY_FILLED
                FILLED
                REJECTED'''

        self.status = status
        self.order_id = order_id
        self.side = side
        self.price = price
        self.size = size
        self.filled_size = 0
        self.first_live_ts_ms = None


class OrderList:
    def __init__(self):
        self.orderlist = {}
        self.filled_position = 0.0
        self.open_position = 0.0
     
    def update_orderlist(self, event_type, order_id, side, price, size, ts_ms):
        # check if there is exisitng order on operations that amends order
        if event_type != 'NEW_SEND' and order_id not in self.orderlist.keys():
            raise ValueError(f"Order {order_id} not found for an order supposed to exist")
        # update order status
        if order_id not in self.orderlist.keys() and event_type == 'NEW_SEND':
            self.orderlist[order_id] = Order('PENDING_NEW', order_id, side, price, size)
        elif event_type == 'NEW_ACK':
            if  self.pass_risk_limit_check():
                self.orderlist[order_id].status ='LIVE'
                self.orderlist[order_id].first_live_ts_ms = ts_ms
                self.open_position += size if side == 'BUY' else - size
            else:
                self.orderlist[order_id].status = 'REJECTED'
        elif event_type == 'CANCEL_SEND' and self.orderlist[order_id].status in ['LIVE', 'PARTIALLY_FILLED']:
            self.orderlist[order_id].status = 'PENDING_CANCEL'
        elif self.orderlist[order_id].size == self.orderlist[order_id].filled_size:
            self.orderlist[order_id].status  == 'FILLED'
            self.filled_position += size if side == 'BUY' else  - size
            self.open_position -= size if side == 'BUY' else + size
        elif event_type == 'CANCEL_ACK' and self.orderlist[order_id].status != 'FILLED':
            self.orderlist[order_id].status = 'CANCELLED'
            self.open_position -= size if side == 'BUY' else self.open_position + size
    
    
    def pass_risk_limit_check(self, side,size):
        if side == 'BUY':
            return self.open_position + self.filled_position + size < max_abs_position
        else:
            return self.open_position + self.filled_position + size < -max_abs_position
        

    def get_order_table(self):
        order_table = pd.DataFrame()
        for order_id, order in self.orderlist.items():
            order_table = order_table.append({
                'order_id': order_id,
                'side': order.side,
                'price': order.price,
                'size': order.size,
                'filled_size': order.filled_size,
                'remaining_qty': order.size - order.filled_size,
                'first_live_ts_ms': order.first_live_ts_ms,
                'final_state': order.final_state,
            })


import pandas as pd

# part A 
def process_event_timeline():
    event_order = ['QUOTE','TRADE','NEW_SEND','NEW_ACK','CANCEL_SEND','CANCEL_ACK']
    market_event_df = pd.read_csv('market_events.csv')
    algo_action_df = pd.read_csv('algo_actions.csv')
#ts_ms,event_type,bid,ask,bid_size,ask_size,trade_price,trade_qty,aggressor_side
    private_event_df = pd.DataFrame()
    for _,row in algo_action_df.iterrrows():
        if row['action'] == 'NEW':
            if row['side'] == 'BUY':
                bid = row['price']
                bid_size = row['qty'] 
                ask = None
                ask_size = None
            else:
                ask = row['price']
                ask_size = row['qty']
                bid = None
                bid_size = None
            #new send
            private_event_df = private_event_df.append({
                'ts_ms': row['send_ts_ms'],
                'event_type': 'NEW_SEND',
                'bid': bid,
                'bid_size': bid_size,
                'ask': ask,
                'ask_size': ask_size,
                'trade_price': None,
                'trade_qty': None,
                'aggressor_side': None,

            })
            #new ack
            private_event_df = private_event_df.append({
                'ts_ms': row['send_ts_ms'] + exchange_latency_ms,
                'event_type': 'NEW_ACK',
                'bid': bid,
                'bid_size': bid_size,
                'ask': ask,
                'ask_size': ask_size,
                'trade_price': None,
                'trade_qty': None,
                'aggressor_side': None,
            })
        elif row['action'] == 'CANCEL':
            order_details = private_event_df[private_event_df['order_id'] == row['order_id']
            if order_details['side'] == 'BUY':
                bid = order_details['price']
                bid_size = order_details['qty'] 
                ask = None
                ask_size = None
            else:
                ask = order_details['price']
                ask_size = order_details['qty']
                bid = None
                bid_size = None & private_event_df['action']== 'NEW']
            #cancel send
            private_event_df = private_event_df.append({
                'ts_ms': row['send_ts_ms'],
                'event_type': 'CANCEL_SEND',
                'bid': bid,
                'bid_size': bid_size,
                'ask': ask,
                'ask_size': ask_size,
                'trade_price': None,
                'trade_qty': None,
                'aggressor_side': None,

            })
            #cancel ack
            private_event_df = private_event_df.append({
                'ts_ms': row['send_ts_ms'] + exchange_latency_ms,
                'event_type': 'CANCEL_ACK',
                'bid': bid,
                'bid_size': bid_size,
                'ask': ask,
                'ask_size': ask_size,
                'trade_price': None,
                'trade_qty': None,
                'aggressor_side': None,
            })
    event_df = pd.concat([market_event_df, private_event_df])
    event_priority = {event_type: i for i, event_type in enumerate(event_order)}
    event_df["event_priority"] = event_df["event_type"].map(event_priority)
    event_df = event_df.sort_values(by=['ts_ms', 'event_priority'])
    event_df.drop(columns=['event_priority'], inplace=True)
    return event_df


#part B
def process_order_state(event_df):
    orderlist = OrderList()
    for _, row in event_df.iterrows():
        orderlist.update_orderlist(row['event_type'], row['order_id'], row['side'], row['price'], row['size'], row['ts_ms'])
    return orderlist.get_order_table()


#part c



def main():
    event_df = process_event_timeline()

if __name__ == '__main__':
    main()

