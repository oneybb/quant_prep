# Mock Live Coding Question: Market-Making Quote Optimization from Fill and Adverse Selection Data

**Summary:**
You are given historical quote attempts, market features, fills, and future mid-price moves. Your task is to estimate fill probability, adverse selection, expected quote value, and choose optimal bid/ask quote distances under inventory risk.

**Focus:**
Market-making math, fill probability, adverse selection, expected value, volatility, inventory skew, spread capture, statistical grouping, and quote selection.

**Difficulty:** Medium-hard
**Suggested time:** 60–75 minutes
**Language:** Python preferred. Pandas/Numpy may help, but the core logic should still be explainable without them.

---

# Problem Context

You are working on a crypto market-making strategy for `BTC-USDT`.

Your strategy places passive bid and ask quotes at different distances from the mid price.

For each historical quote attempt, you know:

* where the quote was placed,
* whether it was filled,
* what the market conditions were,
* and where the mid price moved after the fill.

Your goal is to estimate whether quoting closer or wider is profitable, and how your quote should change when you already have inventory.

---

# Dataset 1: `quote_attempts.csv`

Each row is one quote your strategy attempted to place.

```csv
quote_id,ts_ms,side,mid_price,quote_distance_bps,quote_size,spread_bps,imbalance,vol_1s_bps,filled,fill_ts_ms,fill_price,mid_after_1s
Q1,1000,BUY,100.00,1,0.5,4,0.30,2.0,1,1200,99.99,99.97
Q2,1000,SELL,100.00,1,0.5,4,0.30,2.0,1,1150,100.01,100.04
Q3,2000,BUY,100.02,2,0.5,5,-0.20,2.5,1,2300,100.00,99.96
Q4,2000,SELL,100.02,2,0.5,5,-0.20,2.5,0,,,
Q5,3000,BUY,99.98,3,0.5,6,-0.50,3.5,1,3400,99.95,99.90
Q6,3000,SELL,99.98,3,0.5,6,-0.50,3.5,0,,,
Q7,4000,BUY,100.05,1,0.5,3,0.60,1.8,0,,,
Q8,4000,SELL,100.05,1,0.5,3,0.60,1.8,1,4100,100.06,100.10
Q9,5000,BUY,100.10,2,0.5,5,0.10,2.2,1,5200,100.08,100.07
Q10,5000,SELL,100.10,2,0.5,5,0.10,2.2,1,5350,100.12,100.09
Q11,6000,BUY,100.00,3,0.5,7,-0.70,4.0,1,6500,99.97,99.91
Q12,6000,SELL,100.00,3,0.5,7,-0.70,4.0,0,,,
Q13,7000,BUY,99.92,1,0.5,4,0.40,2.1,0,,,
Q14,7000,SELL,99.92,1,0.5,4,0.40,2.1,1,7300,99.93,99.96
Q15,8000,BUY,100.03,2,0.5,5,-0.10,2.8,1,8400,100.01,99.99
Q16,8000,SELL,100.03,2,0.5,5,-0.10,2.8,1,8250,100.05,100.06
Q17,9000,BUY,100.08,3,0.5,6,0.20,3.0,0,,,
Q18,9000,SELL,100.08,3,0.5,6,0.20,3.0,1,9500,100.11,100.14
Q19,10000,BUY,100.15,1,0.5,3,-0.30,2.4,1,10100,100.14,100.10
Q20,10000,SELL,100.15,1,0.5,3,-0.30,2.4,0,,,
```

---

# Column Definitions

```python
quote_distance_bps
```

means how far your passive quote is from the mid price.

For a BUY quote:

```python
fill_price = mid_price * (1 - quote_distance_bps / 10000)
```

For a SELL quote:

```python
fill_price = mid_price * (1 + quote_distance_bps / 10000)
```

`imbalance` is top-of-book imbalance:

```python
imbalance = (bid_size - ask_size) / (bid_size + ask_size)
```

Interpretation:

* Positive imbalance means bid-side pressure is stronger.
* Negative imbalance means ask-side pressure is stronger.

`vol_1s_bps` is recent short-horizon volatility in basis points.

`mid_after_1s` is the mid price one second after the fill.

If the quote was not filled, `fill_ts_ms`, `fill_price`, and `mid_after_1s` are missing.

---

# Global Parameters

Use:

```python
maker_rebate_bps = 1
max_abs_position = 2.0
current_position = 1.2
inventory_penalty_lambda = 0.4
min_observations_per_bucket = 2
```

Interpretation:

* You earn a 1 bps maker rebate when your quote is filled.
* Your current position is long `1.2 BTC`.
* Maximum absolute position allowed is `2.0 BTC`.
* Since you are already long, buying more should be penalized more than selling.
* `inventory_penalty_lambda` controls how strongly you penalize inventory risk.

---

# Part A: Estimate Fill Probability by Side and Quote Distance

Group the data by:

```python
side
quote_distance_bps
```

For each group, calculate:

```python
num_quotes
num_filled
fill_probability
```

Where:

```python
fill_probability = num_filled / num_quotes
```

Return a table like:

```python
side
quote_distance_bps
num_quotes
num_filled
fill_probability
```

## What this tests

* Groupby aggregation
* Empirical probability estimation
* Understanding that closer quotes usually fill more often
* Recognizing small-sample limitations

---

# Part B: Calculate Realized Post-Fill Edge

For each filled quote, calculate post-fill edge in basis points.

For a BUY fill:

```python
post_fill_edge_bps = (mid_after_1s - fill_price) / fill_price * 10000
```

For a SELL fill:

```python
post_fill_edge_bps = (fill_price - mid_after_1s) / fill_price * 10000
```

Interpretation:

* Positive value means the market moved in your favor after the fill.
* Negative value means adverse selection.

Then calculate the average post-fill edge by:

```python
side
quote_distance_bps
```

Return:

```python
side
quote_distance_bps
avg_post_fill_edge_bps
num_filled
```

## What this tests

* Adverse selection math
* Conditional averaging
* Handling missing values
* Interpreting fill toxicity

---

# Part C: Estimate Expected Value of Each Quote Distance

For each `(side, quote_distance_bps)` bucket, estimate expected value in bps:

```python
expected_value_bps = fill_probability * (avg_post_fill_edge_bps + maker_rebate_bps)
```

Only calculate expected value if:

```python
num_quotes >= min_observations_per_bucket
```

Return:

```python
side
quote_distance_bps
fill_probability
avg_post_fill_edge_bps
maker_rebate_bps
expected_value_bps
```

## What this tests

* Expected value calculation
* Combining probability and conditional payoff
* Maker rebate logic
* Understanding that high fill probability is not always good

---

# Part D: Choose the Best Bid and Ask Quote Distance

Using the expected value table, choose:

```python
best_bid_distance_bps
best_ask_distance_bps
```

Rules:

* For BUY quotes, choose the distance with the highest expected value among `side = BUY`.
* For SELL quotes, choose the distance with the highest expected value among `side = SELL`.
* Ignore buckets with insufficient observations.

Return:

```python
best_bid_distance_bps
best_bid_expected_value_bps
best_ask_distance_bps
best_ask_expected_value_bps
```

Then briefly answer:

> Is the closest quote always the best quote? Why or why not?

## What this tests

* Ranking
* Quote optimization
* Market-making intuition
* Tradeoff between fill probability and adverse selection

---

# Part E: Inventory-Aware Quote Skew

You currently have:

```python
current_position = 1.2
max_abs_position = 2.0
```

You are long BTC, so you want to:

* make BUY quotes less aggressive,
* make SELL quotes more aggressive.

Define inventory ratio:

```python
inventory_ratio = current_position / max_abs_position
```

Define skew size:

```python
inventory_skew_bps = inventory_penalty_lambda * inventory_ratio * average_vol_1s_bps
```

Where:

```python
average_vol_1s_bps = mean(vol_1s_bps)
```

Adjust quote distances as follows.

For BUY quote:

```python
inventory_adjusted_bid_distance_bps = best_bid_distance_bps + inventory_skew_bps
```

For SELL quote:

```python
inventory_adjusted_ask_distance_bps = max(0, best_ask_distance_bps - inventory_skew_bps)
```

Return:

```python
average_vol_1s_bps
inventory_ratio
inventory_skew_bps
inventory_adjusted_bid_distance_bps
inventory_adjusted_ask_distance_bps
```

## What this tests

* Inventory-aware market making
* Risk skew logic
* Volatility-scaled quoting
* Understanding why long inventory means quote more defensively on the bid

---

# Part F: Feature-Based Toxicity Analysis

A quote is considered toxic if it was filled and:

```python
post_fill_edge_bps < 0
```

For filled quotes only, calculate toxicity rate by:

```python
side
imbalance_bucket
vol_bucket
```

Define:

```python
imbalance_bucket = "positive" if imbalance > 0 else "negative"
vol_bucket = "high_vol" if vol_1s_bps >= median(vol_1s_bps) else "low_vol"
```

For each group, calculate:

```python
toxicity_rate = number_of_toxic_fills / number_of_fills
```

Return:

```python
side
imbalance_bucket
vol_bucket
num_fills
toxicity_rate
avg_post_fill_edge_bps
```

## What this tests

* Feature engineering
* Conditional statistics
* Toxic flow analysis
* Market interpretation

---

# Part G: Build a Simple Quote Decision Rule

Using your results, propose a rule that decides whether to quote or not.

For example:

```python
quote_allowed = expected_value_bps > 0 and toxicity_rate < 0.6
```

Your task is to implement a function:

```python
def should_quote(side, quote_distance_bps, imbalance, vol_1s_bps):
    ...
```

The function should return:

```python
True
```

or:

```python
False
```

Use the statistics you calculated from historical data.

Then apply this function to all rows in `quote_attempts.csv` and return:

```python
quote_id
side
quote_distance_bps
imbalance
vol_1s_bps
should_quote
```

## What this tests

* Turning data analysis into a trading rule
* Avoiding overfitting
* Translating statistics into production-style logic
* Explaining why a rule makes sense

---

# Part H: Compare Naive Quoting vs Filtered Quoting

Assume the strategy originally placed every quote in the dataset.

Calculate total realized PnL bps for filled quotes only.

For each filled quote:

For BUY:

```python
realized_edge_bps = (mid_after_1s - fill_price) / fill_price * 10000 + maker_rebate_bps
```

For SELL:

```python
realized_edge_bps = (fill_price - mid_after_1s) / fill_price * 10000 + maker_rebate_bps
```

Calculate:

```python
naive_avg_edge_bps = average realized_edge_bps over all filled quotes
filtered_avg_edge_bps = average realized_edge_bps over filled quotes where should_quote == True
num_quotes_naive
num_quotes_filtered
num_fills_naive
num_fills_filtered
```

Return:

```python
naive_avg_edge_bps
filtered_avg_edge_bps
num_quotes_naive
num_quotes_filtered
num_fills_naive
num_fills_filtered
```

Then answer:

> Did the filter improve average edge? What tradeoff did it create?

## What this tests

* Backtest-style evaluation
* Selection bias awareness
* Strategy comparison
* Practical market-making reasoning

---

# Part I: Final Interpretation Questions

Answer briefly:

1. Which quote distance had the highest expected value for BUY quotes?
2. Which quote distance had the highest expected value for SELL quotes?
3. Did higher fill probability always imply better expected value?
4. Did adverse selection appear worse in high-volatility conditions?
5. How did inventory affect your final bid and ask distances?
6. Would you trust this result in production? Why or why not?
7. What extra data would you want before deploying this strategy?

---

# Expected Solution Structure

A strong solution may include helper functions like:

```python
def compute_post_fill_edge(row):
    if row["filled"] != 1:
        return None

    if row["side"] == "BUY":
        return (row["mid_after_1s"] - row["fill_price"]) / row["fill_price"] * 10000

    if row["side"] == "SELL":
        return (row["fill_price"] - row["mid_after_1s"]) / row["fill_price"] * 10000
```

```python
def estimate_fill_probability(df):
    return (
        df.groupby(["side", "quote_distance_bps"])
          .agg(
              num_quotes=("quote_id", "count"),
              num_filled=("filled", "sum")
          )
          .assign(fill_probability=lambda x: x["num_filled"] / x["num_quotes"])
          .reset_index()
    )
```

```python
def calculate_expected_value(fill_prob_df, edge_df, maker_rebate_bps):
    merged = fill_prob_df.merge(
        edge_df,
        on=["side", "quote_distance_bps"],
        how="left"
    )

    merged["expected_value_bps"] = (
        merged["fill_probability"] *
        (merged["avg_post_fill_edge_bps"] + maker_rebate_bps)
    )

    return merged
```

---

# Why This Is a Good Market-Making Math Interview Question

This question tests a more quantitative side of market making.

| Area               | Tested By                                       |
| ------------------ | ----------------------------------------------- |
| Fill probability   | Empirical fill rates by quote distance          |
| Adverse selection  | Post-fill price movement                        |
| Expected value     | Fill probability multiplied by conditional edge |
| Quote optimization | Choosing best bid/ask distance                  |
| Inventory control  | Volatility-scaled quote skew                    |
| Feature analysis   | Toxicity by imbalance and volatility            |
| Backtesting        | Naive quoting vs filtered quoting               |
| Market intuition   | Understanding why more fills can be worse       |

This fits the interview description:

> "Write code to solve a problem and make sense of data."

It is especially relevant for a market-making role because the core question is:

> Where should I quote, and when should I avoid quoting?
