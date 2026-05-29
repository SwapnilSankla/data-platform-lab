# repartition() vs coalesce() in Apache Spark

# Concept

`repartition()` and `coalesce()` are Spark operations used to change the number of downstream execution partitions.

Although both modify partition counts, they behave very differently internally.

Understanding this distinction is critical for:
- shuffle optimization
- partition tuning
- output file sizing
- reducing unnecessary data movement
- improving distributed execution efficiency

---

# First Principles

Partitions are the unit of:
- distributed execution
- task scheduling
- parallelism

Changing partition count changes:
- number of downstream tasks
- execution topology
- workload distribution

However:

```text
changing partition count
does NOT always mean
physically redistributing all rows
```

This distinction is the key difference between:
- `repartition()`
- `coalesce()`

---

# repartition()

# Definition

`repartition()` performs:

```text
full global redistribution of rows
```

Spark:
1. destroys old partition layout
2. shuffles rows globally
3. creates entirely new partitions

---

# Example

```python
df.repartition(10)
```

Spark:
- redistributes rows across executors
- creates 10 new balanced partitions
- performs full shuffle exchange

---

# Important Internal Behavior

`repartition()` always triggers:

```text
full shuffle exchange
```

This includes:
- shuffle write
- shuffle read
- reducer fetch
- network redistribution

Rows may move:
- from any partition
- to any new partition

---

# Mental Model

Think of:

```python
df.repartition(10)
```

as:

```text
"destroy old partitioning,
rebalance dataset globally"
```

Spark rebuilds the partition layout entirely.

---

# How repartition() Works Internally

Suppose:

```text
200 upstream partitions
```

Now:

```python
df.repartition(2)
```

Spark:
1. hashes rows into new reducer partitions
2. writes shuffle files locally
3. reducers fetch shuffle blocks
4. creates 2 entirely new partitions

This is classic shuffle behavior.

---

# Important Property

After repartition:
- old partition layout no longer matters
- new global partitioning created
- workload balancing improves

This is why repartition:
- is expensive
- but often produces better balance

---

# Common Use Cases

## Rebalancing Skewed Data

```python
df.repartition(200)
```

Improves:
- workload distribution
- cluster utilization

---

## Before Joins/Aggregations

Balanced partitions improve:
- shuffle performance
- parallelism

---

## Partitioning By Key

```python
df.repartition(50, "user_id")
```

Rows with same key tend to land together.

Useful for:
- joins
- aggregations

---

# coalesce()

# Definition

`coalesce()` primarily changes:

```text
how downstream tasks consume partitions
```

without rebuilding the global partition layout.

This is the most important mental model.

---

# Example

```python
df.coalesce(2)
```

Spark tries:
- reducing downstream task count
- collapsing partition consumption
- avoiding full shuffle exchange

---

# Important Internal Behavior

By default:

```python
df.coalesce(2)
```

uses:

```python
shuffle=False
```

Meaning:
- no full shuffle exchange
- no global redistribution
- no reducer fetch protocol

This is fundamentally different from repartition.

---

# The Most Important Insight

`coalesce()` usually does NOT:
- physically reorganize rows
- globally redistribute data
- create entirely new partition layouts

Instead:

```text
fewer downstream tasks
consume multiple upstream partitions
```

This is the core behavior.

---

# Internal Mental Model

Suppose:

```text
200 upstream partitions
```

Now:

```python
df.coalesce(2)
```

Spark may logically schedule:

| Downstream Task | Reads |
|---|---|
| Task A | partitions 0-99 |
| Task B | partitions 100-199 |

Notice:
- upstream partition files remain unchanged
- no full shuffle exchange occurs
- no global row redistribution happens

Spark mostly changes:
- downstream execution topology

This is why coalesce is much cheaper.

---

# Extremely Important Clarification

When people say:

```text
coalesce avoids shuffle
```

they usually mean:

```text
coalesce avoids FULL shuffle exchange
```

This does NOT necessarily mean:
- absolutely zero coordination
- zero remote reads
- zero data movement

But Spark avoids:
- expensive all-to-all redistribution

That is the key distinction.

---

# repartition() vs coalesce()

| Feature | repartition() | coalesce() |
|---|---|---|
| Full shuffle exchange | Yes | Usually No |
| Global redistribution | Yes | No |
| New partition layout | Yes | No |
| Reducer fetch protocol | Yes | Usually No |
| Task count reduction | Yes | Yes |
| Increase partitions | Yes | Not meaningful |
| Decrease partitions | Yes | Yes |
| Balancing quality | Better | Potentially skewed |
| Cost | High | Lower |

---

# Why coalesce() Is Cheaper

Because Spark avoids:
- shuffle write
- shuffle read
- reducer fetch
- global row redistribution
- expensive network exchange

Instead:
- fewer downstream tasks consume existing partitions

This drastically reduces:
- network IO
- disk IO
- shuffle overhead

---

# Important Limitation

Because coalesce preserves original layout:

```text
existing skew may remain
```

Example:

| Partition | Size |
|---|---|
| P1 | 5 GB |
| P2 | 50 MB |

Coalesce may still produce:
- imbalanced downstream tasks

Because rows are NOT globally redistributed.

---

# coalesce(shuffle=True)

Spark also supports:

```python
df.coalesce(2, shuffle=True)
```

This performs:
- actual shuffle exchange
- redistribution behavior closer to repartition

Most engineers rarely use this explicitly.

---

# Increasing vs Decreasing Partitions

## repartition()

Suitable for:
- increasing partitions
- decreasing partitions
- rebalancing workloads

Because Spark rebuilds partition layout globally.

---

## coalesce()

Primarily intended for:

```text
reducing downstream task count cheaply
```

without expensive redistribution.

Not intended for:
- meaningful repartition balancing

---

# Common Usage Patterns

# repartition()

Used when:
- improving balance
- increasing parallelism
- optimizing joins
- handling skew
- redistributing workloads

---

# coalesce()

Used when:
- reducing output file count
- optimizing final writes
- reducing small files
- collapsing excessive partitions

---

# Common Example

```python
df.coalesce(1).write.parquet(...)
```

Goal:
- produce fewer output files

Spark tries:
- reducing downstream write tasks
without:
- globally reshuffling rows

---

# Important Caveat

`coalesce(1)` may:
- destroy parallelism
- bottleneck execution
- overload single task/executor

Dangerous for:
- very large datasets

Usually acceptable only for:
- small outputs
- debugging
- demos

---

# Spark UI Observation

## repartition()

Usually shows:
- shuffle stages
- Exchange operators
- shuffle read/write metrics

---

## coalesce()

Usually shows:
- fewer shuffle operations
- simpler execution plans
- reduced downstream task count

---

# Common Misconceptions

## Misconception 1

Changing partition count always means global redistribution.

Reality:
`coalesce()` often only changes downstream partition consumption.

---

## Misconception 2

`coalesce()` physically merges rows into new partitions.

Reality:
Spark often preserves existing partition layout and changes downstream task topology.

---

## Misconception 3

`coalesce()` means zero data movement.

Reality:
Some coordination or remote reads may still occur.

Spark simply avoids:
- full shuffle exchange protocol

---

## Misconception 4

`repartition()` is always bad.

Reality:
Sometimes repartition dramatically improves:
- balancing
- parallelism
- overall runtime

---

# Most Important Mental Model

## repartition()

```text
Destroy old partitioning,
redistribute rows globally,
create entirely new partition layout
```

---

## coalesce()

```text
Keep existing partition layout mostly intact,
reduce downstream task count,
allow fewer tasks to consume multiple upstream partitions
```

This distinction is foundational for Spark optimization and distributed systems reasoning.

---

# Related Concepts

- Shuffle
- Partitioning
- Narrow vs Wide Transformations
- Jobs, Stages, and Tasks
- Data Skew
- Spark UI
- Adaptive Query Execution
- Shuffle Optimization