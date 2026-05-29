# Narrow vs Wide Transformations

## Concept

Apache Spark transformations can broadly be categorized into:

1. Narrow transformations
2. Wide transformations

The key difference lies in whether data movement (shuffle) is required across partitions.

This distinction is extremely important because shuffle is one of the most expensive operations in distributed systems.

---

# Why This Concept Exists

Spark processes data in distributed partitions.

Some operations can be performed independently within each partition, while others require records from multiple partitions to be grouped together.

This distinction impacts:
- Performance
- Network utilization
- Memory usage
- Number of stages in execution
- Scalability

Understanding narrow vs wide transformations helps reason about:
- Why some jobs are fast
- Why some jobs create additional stages
- Why some jobs trigger shuffle
- Why some jobs become expensive at scale

---

# Narrow Transformations

## Definition

A narrow transformation is a transformation where each output partition depends on data from only a single input partition.

No data movement across partitions is required.

---

# Internal Mental Model

Imagine Spark already divided the dataset into partitions:

```text
Partition 1
Partition 2
Partition 3
```

If a transformation can be executed independently within each partition, then it is narrow.

Examples:
- filter
- select
- withColumn
- map

Each worker processes only its local partition.

No communication between workers is required.

---

# Example

```python
filtered_df = df.filter("event_type = 'purchase'")
```

Spark simply scans each partition locally and filters matching rows.

No shuffle occurs.

---

# Spark Execution Behavior

Typical execution characteristics:
- Usually remains within the same stage
- No shuffle boundary
- No network data movement
- Faster execution
- Better scalability

---

# Common Narrow Transformations

| Transformation | Reason |
|---|---|
| filter | Operates locally on partition |
| select | Column projection only |
| withColumn | Row-wise computation |
| map | Local row transformation |
| flatMap | Local expansion |
| union | Appends partitions |

---

# Wide Transformations

## Definition

A wide transformation is a transformation where output partitions depend on data from multiple input partitions.

Spark must redistribute data across the cluster.

This redistribution is called shuffle.

---

# Internal Mental Model

Suppose data is partitioned like this:

| Partition | event_type |
|---|---|
| P1 | view |
| P2 | purchase |
| P3 | view |

Now consider:

```python
df.groupBy("event_type").count()
```

To compute final counts:
- all `view` records must come together
- all `purchase` records must come together

Spark cannot complete aggregation independently within each partition.

Hence Spark performs:
1. Partial aggregation locally
2. Shuffle data across partitions
3. Final aggregation after redistribution

---

# Multi-Phase Aggregation

Wide transformations often execute in multiple phases.

## Stage 1 — Partial Aggregation

Each partition computes local aggregates.

Example:

| Partition | Local Aggregate |
|---|---|
| P1 | {view: 100} |
| P2 | {purchase: 20} |
| P3 | {view: 80} |

This reduces shuffle size.

---

## Shuffle Boundary

Spark redistributes data using partitioning logic similar to:

```text
hash(key) % number_of_shuffle_partitions
```

This guarantees:
- all matching keys go to the same reducer partition

Important:
A reducer partition may contain multiple keys.

---

## Stage 2 — Final Aggregation

Spark merges partial aggregates:

```text
view → 100 + 80 = 180
```

Final output is generated.

---

# Spark Execution Behavior

Wide transformations usually:
- Create additional stages
- Introduce shuffle boundaries
- Require network communication
- Increase disk and memory usage
- Are more expensive than narrow transformations

---

# Common Wide Transformations

| Transformation | Why Shuffle Is Needed |
|---|---|
| groupBy | Same keys must come together |
| join | Matching keys must align |
| distinct | Duplicate detection across partitions |
| repartition | Explicit redistribution |
| orderBy | Global ordering |
| dropDuplicates | Requires global comparison |

---

# Spark UI Observation

Wide transformations become very visible in Spark UI.

Typical observations:
- Additional stages
- Shuffle Read
- Shuffle Write
- Exchange operators in physical plan

---

# Physical Plan Example

For:

```python
df.groupBy("event_type").count()
```

Spark may generate a plan resembling:

```text
HashAggregate
  Exchange
    HashAggregate
```

Meaning:
1. Partial aggregation
2. Shuffle (Exchange)
3. Final aggregation

This is one of Spark's most fundamental execution patterns.

---

# Performance Implications

## Narrow Transformations
- Faster
- Partition-local
- Minimal network usage
- Better throughput

## Wide Transformations
- More expensive
- Network heavy
- May spill to disk
- Can create skew problems
- Require careful partition tuning

---

# Common Misconceptions

## Misconception 1

Wide transformations always create one partition per key.

Reality:
- Spark hashes keys across reducer partitions
- Multiple keys may exist within same partition

---

## Misconception 2

Shuffle means moving entire raw dataset.

Reality:
Spark often performs partial aggregation before shuffle to reduce data movement.

---

## Misconception 3

`limit()` is a wide transformation.

Reality:
`limit()` itself is not inherently wide, though Spark may still scan multiple partitions to satisfy correctness guarantees.

---

# Operational Impact

Understanding narrow vs wide transformations is critical for:
- Query optimization
- Shuffle tuning
- Partition sizing
- Debugging slow jobs
- Avoiding skew
- Designing scalable pipelines

Most Spark performance issues are ultimately related to:
- Excessive shuffle
- Poor partitioning
- Wide transformation amplification

---

# Related Concepts

- Lazy Evaluation
- Jobs, Stages, and Tasks
- Shuffle
- Partitioning
- Catalyst Optimizer
- Tungsten Engine
- Skew Handling
- Execution Plans