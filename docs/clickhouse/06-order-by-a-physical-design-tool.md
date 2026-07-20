## 6.1 The Table You Designed

Let’s say you’re designing a core table:

```
ride_events(
    request_id,
    rider_id,
    driver_id,
    city_id,
    request_time,
    fare,
    status
)
```

This table powers:

- Dashboards (time-based trends)
- City-level analysis
- Driver performance queries
- Rider lookups (occasionally)

---

You now need to define:

```
ORDERBY ( ? )
```

---

## 🤔 Pause

What would you choose?

Don’t rush — this is one of the most important decisions in ClickHouse.

---

## 6.2 The First Instinct

A common instinct is:

> “Let’s include the most important fields”
> 

So you might write:

```
ORDERBY (rider_id, driver_id, city_id, request_time)
```

Or even:

```
ORDERBY (request_time, city_id, driver_id, rider_id)
```

Feels safe.

Feels flexible.

---

## ❌ The Hidden Assumption

This assumes:

> ORDER BY behaves like a multi-column index in OLTP systems.
> 

But it doesn’t.

---

## 6.3 What ORDER BY Actually Does

In ClickHouse, ORDER BY defines:

> The **physical layout of data on disk**
> 

When data is written:

- Rows are sorted by ORDER BY
- Stored in that order
- Granules follow this order
- Index reflects this order

---

So:

> ORDER BY is not an index.
> 
> 
> It is **how your data is physically arranged**.
> 

---

## 6.4 The Prefix Rule (Revisited Deeply)

Let’s say you choose:

```
ORDERBY (request_time, city_id)
```

Data is physically grouped like:

```
time1 → cityA
time1 → cityB
time2 → cityA
time2 → cityB
...
```

---

## 🤔 Pause

Now consider this query:

```
WHERE request_timeBETWEEN XAND Y
```

Efficient or not?

---

### Answer

Very efficient.

Because:

- Data is contiguous in time
- Binary search on primary index works well
- Few granules read

---

## 6.5 Now Change the Query

```
WHERE city_id=5
```

---

## 🤔 Pause

Efficient or not?

---

### Answer

Not efficient.

Because:

- city_id is not leading key
- Data is scattered across time
- Many granules must be scanned

---

## 💡 Insight

> ORDER BY only helps if your filter aligns with its **prefix**
> 

---

## 6.6 Let’s Flip the Design

Now try:

```
ORDERBY (city_id, request_time)
```

Data looks like:

```
cityA → time1, time2, time3...
cityB → time1, time2, time3...
```

---

## 🤔 Pause

Now evaluate:

### Query 1

```
WHERE city_id=5AND request_timeBETWEEN XAND Y
```

### Query 2

```
WHERE request_timeBETWEEN XAND Y
```

---

### Answers

Query 1 → very efficient

Query 2 → less efficient

---

## 6.7 The Real Tradeoff

You cannot optimize for everything.

You must choose:

> Which queries deserve physical locality?
> 

---

## 6.8 Your Workload (Ride Events)

Let’s say your workload is:

- 60% → time-only queries
- 25% → city + time
- 10% → driver + time
- 5% → rider lookups

---

## 🤔 Pause

Which ORDER BY would you choose?

---

## 6.9 The Tempting Answer

You might think:

> “City has skew (top 3 cities = 70% traffic), so let’s use city first”
> 

```
ORDERBY (city_id, request_time)
```

---

## ❌ Why This Is Risky

Let’s analyze.

---

### Compression Argument

Yes:

- City clustering improves RLE
- High skew helps compression

---

But:

### Time Column Behavior

With:

```
ORDERBY (city_id, request_time)
```

Time becomes:

- Non-monotonic globally
- Reset within each city

This hurts:

- Delta encoding
- Compression
- Merge efficiency

---

## 🤯 Hidden Cost

You optimized one column (city),

but degraded another (time) — often a larger column.

---

## 6.10 The Correct Reasoning

Given workload:

- 60% queries are time-based
- Data arrives time-ordered

Best choice:

```
ORDERBY (request_time, city_id)
```

---

## 💡 Insight

> Optimize for the dimension that dominates **data scanned**, not just frequency.
> 

---

## 6.11 What About Driver Queries?

Query:

```
WHERE driver_id= XAND request_timeBETWEEN ...
```

---

## 🤔 Pause

Will ORDER BY help?

---

### Answer

Not much.

Because:

- driver_id not in prefix
- data scattered

---

## 6.12 The Realization

ORDER BY cannot serve all access patterns.

So what do you do?

---

## 6.13 The Options

For driver queries:

1. Accept slower performance
2. Use projections
3. Use pre-aggregated tables
4. Use skipping indexes

---

This introduces a layered design (we’ll revisit later).

---

## 6.14 A Subtle but Critical Insight

ORDER BY also affects:

- Merge efficiency
- Compression
- Insert cost

Not just queries.

---

## 🤔 Think

If data arrives sorted by time…

And ORDER BY starts with time…

What happens during insert?

---

### Answer

Minimal reshuffling → efficient ingestion.

---

## 6.15 If You Misalign ORDER BY

Example:

```
ORDERBY (city_id, request_time)
```

But data arrives time-ordered.

Now:

- Insert must reshuffle data
- Merge cost increases
- CPU increases

---

## 💡 Insight

> Good ORDER BY aligns with **both query patterns and ingestion order**
> 

---

## 6.16 The Prefix Law (Final Form)

For:

```
ORDERBY (A, B, C)
```

You get strong pruning only when:

- A is filtered
- A + B are filtered

Everything else is degraded.

---

## 6.17 Stress Test

Suppose you choose:

```
ORDERBY (request_time, city_id)
```

Now consider:

```
WHERE city_id=5AND request_timeBETWEEN ...
```

Efficient?

---

### Answer

Yes — because:

- request_time prunes first
- city_id refines within range

---

## 6.18 Final Mental Model

ORDER BY defines:

```
Physical clustering → Index structure → Compression → Merge behavior
```

---

## 6.19 Closing Insight

If you remember one thing:

> ORDER BY is not a query optimization hint.
> 
> 
> It is the **physical shape of your data on disk**.
>