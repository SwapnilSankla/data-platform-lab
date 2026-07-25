# Sort Merge Join in Apache Spark

## Why Joins Are Hard in Distributed Systems

Suppose we have two datasets:

### Events Dataset

| user_id | event_type |
| ------- | ---------- |
| 1       | click      |
| 2       | view       |

### Users Dataset

| user_id | country |
| ------- | ------- |
| 1       | IN      |
| 2       | US      |

In a distributed cluster:

* rows from both datasets may exist on different executors
* Spark cannot directly join them

Before joining:

* matching keys must be colocated together

This is the core distributed join problem.

---

## Two Fundamental Distributed Join Strategies

Distributed systems generally solve joins using one of two approaches:

| Strategy       | Idea                               |
| -------------- | ---------------------------------- |
| Shuffle Join   | Move matching keys together        |
| Broadcast Join | Replicate small dataset everywhere |

`SortMergeJoin` is Spark's default shuffle-based join strategy for large datasets.

---

## Example Pipeline

```python
from pyspark.sql import SparkSession

events_df = spark.read.csv(
    "s3a://clickstream/2019-Nov.csv",
    header=True
)

users_df = spark.read.parquet(
    "s3a://users/users.parquet"
)

joined_df = events_df.join(
    users_df,
    "user_id"
)

joined_df.count()
```

---

## Physical Plan

```text
== Physical Plan ==
AdaptiveSparkPlan
+- == Final Plan ==
   * HashAggregate
   +- ShuffleQueryStage
      +- Exchange
         +- * HashAggregate
            +- * Project
               +- * SortMergeJoin
                  :- * Sort
                  :  +- AQEShuffleRead
                  :     +- ShuffleQueryStage
                  :        +- Exchange
                  :           +- * Filter
                  :              +- Scan csv
                  +- * Sort
                     +- AQEShuffleRead
                        +- ShuffleQueryStage
                           +- Exchange
                              +- * Filter
                                 +- * ColumnarToRow
                                    +- Scan parquet
```

---

## Initial Plan vs Final Plan

Spark physical plans exist in two forms:

| Plan Type    | Meaning                                  |
| ------------ | ---------------------------------------- |
| Initial Plan | Optimizer's intended execution strategy  |
| Final Plan   | Runtime AQE-optimized execution strategy |

Before execution:

* Spark only knows estimated statistics

During execution:

* AQE collects actual runtime statistics
* Spark may optimize partitioning and execution strategies dynamically

This is why Spark shows:

```text
AdaptiveSparkPlan
```

and:

```text
isFinalPlan=true
```

after execution completes.

---

## Step-by-Step Execution Walkthrough

### 1. Scan Source Data

Spark first scans both datasets.

#### Events Dataset

```text
Scan csv
```

#### Users Dataset

```text
Scan parquet
```

---

#### Important Observation: CSV vs Parquet

CSV scan:

```text
Batched: false
```

Parquet scan:

```text
Batched: true
```

Why?

Parquet supports:

* vectorized columnar reads

CSV does not.

This is one major reason why Parquet significantly outperforms CSV.

---

### 2. Catalyst Adds Null Filters

Spark automatically inserts:

```text
Filter isnotnull(user_id)
```

on both sides.

Why?

Because:

* null values cannot efficiently participate in equality joins

This optimization is automatically added by Catalyst.

---

### 3. Exchange — Shuffle Boundary

Spark then performs:

```text
Exchange
Arguments: hashpartitioning(user_id, 200)
```

This is the most important distributed phase.

Spark repartitions BOTH datasets using:

```text
hash(user_id) % 200
```

This guarantees:

```text
same user_ids land in same partition
```

This is the core requirement for distributed joins.

---

#### Extremely Important Clarification

`Exchange` is a logical shuffle boundary.

It does NOT literally mean:

* Spark immediately pushes rows over network

Instead it means:

```text
data must be redistributed by key
```

---

#### Actual Shuffle Mechanics

Shuffle internally happens in two phases.

---

#### Map-Side Shuffle Phase

Map-side tasks:

1. read rows
2. hash rows by partition key
3. write shuffle files LOCALLY

Example:

```text
Executor A:
  partition-0.data
  partition-1.data
  partition-2.data
```

At this point:

* reducers have NOT fetched anything yet

---

#### Reduce-Side Shuffle Phase

Reducer tasks later:

1. contact all executors
2. fetch required shuffle partitions
3. merge fetched data locally

This means Spark shuffle is fundamentally:

```text
pull-based
```

NOT:

* push-based

This design comes from Hadoop MapReduce architecture.

---

#### Important Mental Model

```text
Exchange
=
logical repartitioning boundary

Internally implemented via:
  map-side shuffle writes
  +
  reducer-side shuffle fetches
```

This is one of the most important Spark internals concepts.

---

### 4. ShuffleQueryStage

After shuffle writes complete, Spark creates:

```text
ShuffleQueryStage
```

This represents:

* materialized shuffle output
* a stable shuffle boundary
* runtime statistics collection point

Example:

```text
Statistics(sizeInBytes=2.0 GiB, rowCount=6.75E+7)
```

Spark now knows:

* actual shuffle size
* actual row counts

This information is used by AQE.

---

### 5. AQEShuffleRead

Spark then performs:

```text
AQEShuffleRead
Arguments: coalesced
```

This means:

* AQE dynamically reduced shuffle partition count

Instead of:

* reading all original shuffle partitions

Spark may:

* merge tiny partitions together

This improves:

* scheduling overhead
* tiny task inefficiency
* resource utilization

---

### 6. Sort Within Partition

After reducers fetch shuffle data:

Spark performs:

```text
Sort
```

Important:

Sorting happens:

```text
within EACH partition
```

NOT:

* globally across cluster

This distinction is extremely important.

---

#### Why Sorting Is Required

Once both datasets are:

* partitioned identically
* sorted by join key

Spark can perform:

```text
sequential merge join
```

similar to:

* merge step in merge sort

This approach is:

* memory efficient
* scalable
* streaming-friendly

---

### 7. SortMergeJoin Execution

Now both sides contain:

* matching partition topology
* sorted rows

Spark can perform local merge join execution.

Important:

```text
network movement already completed earlier
```

during:

* Exchange / shuffle phase

The actual `SortMergeJoin` operator is:

* local CPU computation
* not network transfer

---

#### Extremely Important Distinction

| Phase          | Purpose                    |
| -------------- | -------------------------- |
| Exchange       | Distributed data movement  |
| AQEShuffleRead | Reducer-side shuffle fetch |
| Sort           | Local ordering             |
| SortMergeJoin  | Local merge computation    |

This is a foundational Spark execution concept.

---

### 8. ColumnarToRow

Parquet scan shows:

```text
ColumnarToRow
```

Why?

Parquet internally uses:

* columnar vectorized representation

But:

* SortMergeJoin operates on row-based execution

Spark therefore converts:

* columnar batches
  → rows

This becomes important later while learning:

* Tungsten
* vectorized execution
* whole-stage codegen

---

### 9. Count Aggregation

The query ends with:

```python
joined_df.count()
```

Spark implements this using distributed aggregation.

---

### Partial Aggregation

Each partition first computes:

```text
partial_count
```

locally.

This reduces:

* network traffic
* shuffle volume

---

### Final Aggregation

Spark then performs:

```text
Exchange
Arguments: SinglePartition
```

This gathers:

* all partial counts
* into a single reducer partition

Then Spark computes:

```text
final count
```

This is a classic distributed aggregation pattern.

---

## Why SortMergeJoin Scales Well

Unlike large hash joins:

* SortMergeJoin does not require huge in-memory hash tables

Instead Spark:

* streams through sorted datasets sequentially

This makes it:

* more memory efficient
* better for very large datasets

---

## Why SortMergeJoin Is Expensive

Even though merge computation itself is efficient:

shuffle is extremely expensive because Spark must:

* serialize rows
* partition rows
* spill to disk
* transfer data across network
* fetch remote shuffle blocks
* merge shuffle files
* sort reducer partitions

Most join cost usually comes from:

```text
shuffle
```

NOT:

* merge computation itself

---

## Most Important Mental Models

### 1. Distributed Joins Mean Colocating Keys

```text
matching keys must land together
```

This is the core distributed join requirement.

---

### 2. Exchange Is Logical

`Exchange` represents:

* repartitioning intent

Internally implemented via:

* map-side shuffle writes
* reducer-side shuffle fetches

---

### 3. Shuffle Is Pull-Based

Reducers:

* fetch shuffle blocks from executors

Spark shuffle is fundamentally:

* reducer pull driven

---

### 4. Sort Happens After Shuffle Fetch

Sorting occurs:

* on reducer side
* after partitions are fetched

NOT:

* before network transfer

---

### 5. SortMergeJoin Itself Is Local

Actual join computation:

* happens locally
* after shuffle completes

---

### 6. AQE Optimizes Runtime Execution

AQE can:

* coalesce partitions
* optimize shuffle reads
* dynamically adapt execution

based on:

* actual runtime statistics

---

### 7. Most Join Cost Comes From Shuffle

The expensive part is:

* network movement
* disk spill
* shuffle management

NOT:

* merge computation itself

---

## Related Concepts

* Shuffle
* AQE
* Partitioning
* BroadcastHashJoin
* ShuffleHashJoin
* Repartition vs Coalesce
* Spark Physical Plans
* Spark UI
