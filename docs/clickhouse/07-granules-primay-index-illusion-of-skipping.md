## 7.1 A Query That “Should Be Fast”

Let’s go back to your `ride_events` table:

```
ORDERBY (request_time, city_id)
```

Now consider this query:

```
SELECT*
FROM ride_events
WHERE rider_id=123456
```

---

## 🤔 Pause

Your intuition might say:

> “We have an index, so it should be fast.”
> 

But we already know:

- rider_id is not in ORDER BY prefix
- So primary index won’t help much

---

So you think:

> “Let’s add a bloom filter index.”
> 

```
INDEX rider_bf rider_id TYPE bloom_filter(0.01)
```

---

Now ask:

> Will this query be fast?
> 

---

## 7.2 The Comfortable but Wrong Mental Model

Most people think:

> “Index → jump directly to data”
> 

That’s true in OLTP systems.

But ClickHouse is not doing:

- Row-level indexing
- Pointer chasing

Instead, it works in **blocks (granules)**.

---

## 7.3 What Is a Granule (Precisely)

Inside each part:

- Data is sorted by ORDER BY
- Then divided into chunks of:

```
index_granularity ≈ 8192 rows
```

Each granule:

- Contains ~8192 rows
- Is the smallest unit of data skipping

---

## 7.4 What the Primary Index Stores

For each granule:

- Store the **first ORDER BY key**

Example:

```
Granule 1 → (time=10:00, city=1)
Granule 2 → (time=10:05, city=2)
Granule 3 → (time=10:10, city=1)
...
```

---

This means:

> Primary index is sparse and prefix-based
> 

---

## 7.5 How Query Execution Actually Works

Let’s trace the flow.

---

### Step 1 — Partition Pruning

Skip partitions based on partition key.

---

### Step 2 — Part Selection

Each part is considered independently.

---

### Step 3 — Primary Index Pruning

Binary search on **ORDER BY prefix only**

---

### Step 4 — Granule Filtering

Selected granules are read.

---

### Step 5 — Actual Filtering

Row-level filtering happens after reading.

---

## 💡 Critical Insight

> ClickHouse skips **granules**, not rows.
> 

---

## 7.6 Now Let’s Analyze rider_id Query

We have:

- rider_id not in ORDER BY
- Uniform distribution

So:

- Primary index cannot prune
- Every granule is a candidate

---

## 🤔 Pause

How many granules are we talking about?

---

## 7.7 Let’s Do the Math

Assume:

- Total rows = 10 billion
- Granule size = 8192

Number of granules:

```
10,000,000,000 / 8192 ≈ 1.2 million granules
```

---

Now:

Each granule has ~8192 rows.

Total distinct riders:

```
~200 million riders
```

---

So expected riders per granule:

```
8192 / 200,000,000 ≈ 0.004%
```

Very sparse.

---

## 7.8 Now Add Bloom Filter

For each granule:

- Bloom filter checks if rider might exist

Let’s say query:

```
WHERE rider_idIN (1000 riders)
```

---

## 🤔 Pause

What fraction of granules will pass the bloom filter?

---

## 7.9 The Probability Calculation

Probability a given rider exists in a granule:

```
p = 8192 / 200,000,000 ≈ 0.00004
```

For 1000 riders:

Probability at least one exists:

```
P = 1 - e^(-1000 × p)
  ≈ 1 - e^(-0.04)
  ≈ 4%
```

---

## 7.10 What Does That Mean?

Out of:

```
1.2 million granules
```

We scan:

```
~4% ≈ 48,000 granules
```

Rows scanned:

```
48,000 × 8192 ≈ 400 million rows
```

---

## 🤯 Reality Check

You asked for 1000 riders.

But you scanned 400 million rows.

---

## 💡 Insight

> Bloom filters reduce IO probabilistically — but cannot eliminate it.
> 

---

## 7.11 Why This Happens

Because:

- Bloom filter works per granule
- Granules contain multiple values
- IN queries increase probability of match

---

## 7.12 The Illusion of Skipping

At a high level:

- You feel like you’re “filtering data”
- But you’re actually filtering **granules probabilistically**

---

## 7.13 Now Compare With Projection

If you had:

```
PROJECTION (rider_id, request_time)
```

Data physically sorted by rider_id.

Now:

- Binary search per rider
- Very few granules read

---

## 🤔 Pause

What is the difference?

---

### Answer

Projection gives:

> Deterministic pruning
> 

Bloom filter gives:

> Probabilistic pruning
> 

---

## 7.14 Granule Size Tradeoff (Deep Dive)

Recall:

```
default = 8192 rows
```

---

### If you reduce to 2048:

Pros:

- Smaller granules
- Better skipping precision

Cons:

- 4× more granules
- 4× larger primary index
- More metadata scans

---

## 🤔 Think

Does this reduce bloom filter scanning?

---

### Answer

Yes — but increases metadata cost.

---

## 7.15 Another Subtlety

Granules are not stored independently.

So:

- Even if you skip many granules
- You still pay cost for:
    - Index scanning
    - Metadata traversal

---

## 7.16 Why Primary Index Is Powerful (When Used Correctly)

If query matches ORDER BY prefix:

Example:

```
WHERE request_timeBETWEEN XAND Y
```

Then:

- Binary search finds exact granules
- No probabilistic scanning
- Minimal IO

---

## 💡 Insight

> Primary index is exact but limited
> 
> 
> Bloom filter is flexible but approximate
> 

---

## 7.17 The Cardinality Trap

You earlier asked:

> “Riders have low activity — does bloom help?”
> 

Now you see:

- High cardinality helps
- But uniform distribution hurts

Because:

- Values spread across granules
- Hard to isolate

---

## 7.18 Final Mental Model

Think of ClickHouse as:

```
Granule-level system, not row-level system
```

All skipping decisions happen at granule level.

---

## 7.19 Closing Insight

If you remember one thing:

> ClickHouse does not jump to rows —
> 
> 
> it narrows down to granules and then scans within them.
>