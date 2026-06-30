# Caching and Persistence

## Concept

Apache Spark uses lazy evaluation.

Transformations build lineage (logical execution plans), but Spark does not automatically materialize intermediate results.

This means Spark may recompute the same lineage repeatedly for multiple actions.

Caching and persistence allow Spark to reuse previously computed results instead of recomputing them again.

---

# Why This Concept Exists

Spark is fundamentally designed as:

```text
immutable distributed computation graph
```

Transformations:
- do not mutate data
- do not materialize outputs
- only build lineage

This gives Spark:
- fault tolerance
- optimization flexibility
- execution planning advantages

However, repeated recomputation can become expensive.

Caching solves this problem.

---

# Internal Mental Model

Suppose we write:

```python
filtered = df.filter("event_type = 'purchase'")
```

At this point:
- no computation occurs
- no data is stored
- only lineage exists

Now:

```python
filtered.count()

filtered.groupBy("brand").count()
```

Without caching:
- Spark may replay the entire lineage twice
- CSV may be scanned twice
- filter transformation may execute twice

This happens because:
- transformations are lazy
- lineage is replayable
- actions are independent execution triggers

---

# Extremely Important Learning

## Physical Plans Are Generated Per Action

This is one of Spark's most important conceptual behaviors.

Suppose we execute:

```python
filtered.count()
```

Spark generates:
- one optimized physical plan
- one execution DAG
- one set of jobs/stages/tasks

Later:

```python
filtered.groupBy("brand").count()
```

Spark generates:
- another physical plan
- another execution DAG
- another set of jobs/stages/tasks

Spark does NOT maintain:
- notebook-wide execution plans
- dataframe-wide execution history

Instead:

```text
physical plans are action-scoped
```

This means:
- every action may independently replay lineage
- unless intermediate results are cached/persisted

This is a foundational Spark mental model.

---

# cache()

## Definition

`cache()` tells Spark:

```text
"If this DataFrame is computed, keep the computed partitions in memory for reuse."
```

---

# Important Behavior

## cache() Is Also Lazy

This surprises many engineers initially.

Example:

```python
filtered.cache()
```

At this point:
- nothing is cached yet
- no execution occurs

Spark only marks the DataFrame as cacheable.

Actual caching happens only when an action executes.

---

# Materialization Flow

```python
filtered.cache()

filtered.count()
```

Now Spark:
1. Executes lineage
2. Computes partitions
3. Stores partitions in cache memory

Subsequent actions may reuse cached partitions.

---

# Example

## Without Cache

```python
filtered = df.filter("event_type = 'purchase'")

filtered.count()

filtered.groupBy("brand").count().show()
```

Possible behavior:
- CSV scanned twice
- filter recomputed twice

---

## With Cache

```python
filtered = df.filter("event_type = 'purchase'")

filtered.cache()

filtered.count()

filtered.groupBy("brand").count().show()
```

Possible behavior:
- CSV scanned once
- filtered partitions reused
- second action faster

---

# Physical Plan Observation

Without cache, physical plan may contain:

```text
FileScan csv
```

After cache materialization, physical plan may contain:

```text
InMemoryTableScan
```

This is the strongest indicator that Spark is using cached partitions instead of re-reading the source dataset.

---

# persist()

## Definition

`persist()` is a generalized version of `cache()`.

While:

```python
df.cache()
```

is equivalent to:

```python
df.persist(StorageLevel.MEMORY_ONLY)
```

`persist()` allows explicit control over storage strategy.

---

# Common Storage Levels

| Storage Level | Behavior |
|---|---|
| MEMORY_ONLY | Store only in memory |
| MEMORY_AND_DISK | Spill to disk if memory insufficient |
| DISK_ONLY | Store only on disk |
| MEMORY_ONLY_SER | Serialized in-memory storage |
| OFF_HEAP | Off-heap storage |

---

# Why Persistence Matters

Caching improves:
- repeated computations
- iterative algorithms
- machine learning workloads
- interactive analytics
- repeated aggregations

Without persistence:
- Spark repeatedly replays lineage
- repeated scans become expensive
- shuffle operations repeat unnecessarily

---

# Spark UI Observation

Caching becomes visible in:
- Storage tab
- SQL/DataFrame tab
- Physical plans

You may observe:
- cached partition count
- memory usage
- reduced execution times
- fewer repeated scans

---

# Important Clarification

Caching does NOT remove lineage.

Spark still maintains:
- logical plan
- fault tolerance metadata

Cache simply introduces:
- reusable materialization points

This is important for Spark's resiliency model.

---

# Common Misconceptions

## Misconception 1

`cache()` immediately stores data.

Reality:
Caching itself is lazy.

---

## Misconception 2

Caching removes lineage.

Reality:
Spark still maintains lineage for fault recovery.

---

## Misconception 3

Caching always improves performance.

Reality:
Caching may:
- consume large memory
- increase GC pressure
- become slower for one-time workloads

---

## Misconception 4

Physical plans are generated once per notebook.

Reality:

```text
physical plans are generated per action
```

This is one of Spark's most important execution behaviors.

---

# Operational Impact

Understanding caching and persistence is critical for:
- performance optimization
- iterative processing
- avoiding recomputation
- efficient memory usage
- Spark debugging
- understanding Spark UI

Improper caching may:
- waste executor memory
- increase GC pauses
- destabilize workloads

Effective caching is one of the most important Spark optimization skills.

---

# Related Concepts

- Lazy Evaluation
- Transformations vs Actions
- DAG Lineage
- Jobs, Stages, and Tasks
- Shuffle
- Spark UI
- Partitioning
- Catalyst Optimizer