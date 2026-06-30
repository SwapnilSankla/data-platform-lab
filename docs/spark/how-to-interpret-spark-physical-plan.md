# How to Interpret Spark Physical Plans

# Why This Matters

One of the biggest mindset shifts in Apache Spark is understanding:

```text
your Spark code is NOT executed line-by-line
```

Instead:
- Spark builds a logical computation graph
- Catalyst optimizer rewrites the graph
- Spark generates an optimized physical execution plan
- Adaptive Query Execution (AQE) may further optimize execution during runtime

Understanding physical plans is one of the most important Spark engineering skills because it allows you to:
- identify shuffles
- detect expensive operations
- understand execution stages
- debug performance bottlenecks
- reason about distributed execution

---

# Example Pipeline

We will use the following pipeline which:
1. Reads clickstream CSV data
2. Extracts unique users
3. Generates a country column
4. Writes the output to Parquet in MinIO

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
import os

minio_access_key = os.getenv("MINIO_ACCESS_KEY")
minio_secret_key = os.getenv("MINIO_SECRET_KEY")

spark = SparkSession \
    .builder \
    .appName("generate-user-dimension-dataset") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", minio_access_key) \
    .config("spark.hadoop.fs.s3a.secret.key", minio_secret_key) \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .getOrCreate()

df = spark \
    .read \
    .option("header", "true") \
    .option("inferSchema", "false") \
    .csv("s3a://clickstream/2019-Nov.csv")

user_dimension = df \
    .select("user_id") \
    .distinct() \
    .withColumn("user_id_int", col("user_id").cast("long")) \
    .withColumn("country", 
                when((col("user_id_int") % 5) == 1, "IN")
                .when((col("user_id_int") % 5) == 2, "US")
                .when((col("user_id_int") % 5) == 3, "UK")
                .when((col("user_id_int") % 5) == 4, "CA")
                .otherwise("BR")) \
    .drop("user_id_int")

user_dimension.write.parquet("s3a://users/users.parquet")

spark.stop()
```

---

# Generated Physical Plan

```text
== Physical Plan ==
AdaptiveSparkPlan (16)
+- == Final Plan ==
   Execute InsertIntoHadoopFsRelationCommand (9)
   +- WriteFiles (8)
      +- * Project (7)
         +- * HashAggregate (6)
            +- AQEShuffleRead (5)
               +- ShuffleQueryStage (4), Statistics(sizeInBytes=298.6 MiB, rowCount=9.78E+6)
                  +- Exchange (3)
                     +- * HashAggregate (2)
                        +- Scan csv  (1)
+- == Initial Plan ==
   Execute InsertIntoHadoopFsRelationCommand (15)
   +- WriteFiles (14)
      +- Project (13)
         +- HashAggregate (12)
            +- Exchange (11)
               +- HashAggregate (10)
                  +- Scan csv  (1)
```

---

# Initial Plan vs Final Plan

This is one of the most important modern Spark concepts.

Spark first generates:

```text
Initial Plan
```

This is:
- Spark's best static guess before execution starts

However, after execution begins:
- Spark collects runtime statistics
- Spark may dynamically optimize execution

This produces:

```text
Final Plan
```

This process is called:

```text
Adaptive Query Execution (AQE)
```

---

# Important AQE Insight

Notice this operator:

```text
AQEShuffleRead
```

This means:
- AQE dynamically optimized the shuffle stage during runtime

Spark observed:
- actual shuffle size
- actual row count
- partition statistics

Then:
- optimized downstream execution

---

# Reading Physical Plans Correctly

Physical plans should be interpreted as:

```text
distributed execution graph
```

NOT:
- line-by-line execution of your code

Spark aggressively:
- rewrites operations
- fuses transformations
- removes unnecessary columns
- minimizes shuffle
- optimizes partitioning

---

# Understanding Each Stage

---

# (1) Scan CSV

```text
Scan csv
```

Purpose:
- Read the CSV source file

Important optimization:

```text
ReadSchema: struct<user_id:string>
```

Spark performed:

```text
column pruning
```

Only the required column:
- `user_id`

was read from the CSV.

All other columns were skipped.

This is a major optimization.

---

# (2) HashAggregate (Partial Aggregation)

```text
HashAggregate
```

This stage corresponds to:

```python
.select("user_id").distinct()
```

Spark internally rewrites:

```sql
DISTINCT user_id
```

into:
- aggregation by key

---

# Most Important Insight

This is:

```text
partial local aggregation
```

Spark tries to:
- remove duplicates locally inside each partition
BEFORE shuffle happens.

This reduces:
- shuffle volume
- network traffic
- shuffle file size

This is a critical distributed systems optimization.

---

# (3) Exchange

```text
Exchange
Arguments: hashpartitioning(user_id, 200)
```

This is the shuffle boundary.

Spark now:
- redistributes rows across the cluster
- partitions data by `user_id`

Why?

Because:
- global DISTINCT requires all matching user_ids to land together

This is one of the most important distributed systems principles:

```text
rows with same key
must eventually land together
```

This exact same principle is later used in:
- joins
- aggregations
- groupBy operations

---

# (4) ShuffleQueryStage

```text
ShuffleQueryStage
```

This operator appears because:
- Adaptive Query Execution (AQE) is enabled

This represents:

```text
completed shuffle output
```

Meaning:
1. map-side shuffle completed
2. shuffle files materialized
3. runtime statistics collected

Notice:

```text
Statistics(sizeInBytes=298.6 MiB, rowCount=9.78E+6)
```

Spark now knows:
- actual shuffle size
- actual row count

AQE uses this information for runtime optimization.

---

# (5) AQEShuffleRead

```text
AQEShuffleRead
Arguments: coalesced
```

This is one of the most important observations in the plan.

Initially:
- Spark planned 200 shuffle partitions

However AQE realized:
- 298 MB data does not require 200 downstream tasks

So Spark dynamically:
- coalesced shuffle partition consumption

---

# Extremely Important Clarification

Spark did NOT:
- physically merge shuffle files into one huge partition

Instead Spark:
- reduced downstream task count

This is conceptually similar to:

```python
coalesce()
```

Spark optimized:
- downstream execution topology
- task granularity

This reduced:
- scheduling overhead
- tiny reducer tasks

---

# (6) HashAggregate (Final Aggregation)

```text
HashAggregate
```

This is the:

```text
final global aggregation
```

Now:
- all matching user_ids are colocated after shuffle

Spark can finally:
- compute DISTINCT globally

---

# Important Distributed Aggregation Pattern

Spark commonly performs distributed aggregation in 3 phases:

| Phase | Purpose |
|---|---|
| Partial aggregate | Local reduction before shuffle |
| Shuffle | Bring matching keys together |
| Final aggregate | Global reduction |

This pattern appears repeatedly in Spark.

---

# Additional Observation

Notice this expression:

```text
cast(user_id as bigint)
```

Spark fused:
- type casting
into the same aggregation stage.

Catalyst optimizer aggressively combines operations.

---

# (7) Project

```text
Project
```

This stage generates:

```python
country
```

using:

```python
CASE WHEN ...
```

logic.

This is:
- a narrow transformation
- no shuffle required

---

# Important Observation About drop()

Notice:
- no explicit `drop(user_id_int)` operator exists

Why?

Because Catalyst optimizer realized:
- `user_id_int` is only an intermediate expression
- final output does not require it

So Spark:
- eliminated it automatically

This is a very important Spark optimization behavior.

---

# Most Important Spark Concept

Spark DataFrame code is:

```text
declarative
```

NOT:
- imperative line-by-line execution

Spark optimizes:
- the computation graph itself

---

# (8) WriteFiles

```text
WriteFiles
```

Spark now:
- writes Parquet output files

Important relationship:

```text
number of partitions
≈ number of output files
```

This is a very important data engineering concept.

---

# (9) ExecuteInsertIntoHadoopFsRelationCommand

```text
ExecuteInsertIntoHadoopFsRelationCommand
```

This is:
- final filesystem-backed datasource write operation

Spark commits:
- generated Parquet files
to:
- MinIO

---

# Biggest Lessons From This Plan

# 1. DISTINCT Is Expensive

DISTINCT requires:
1. local aggregation
2. shuffle
3. global aggregation

This makes DISTINCT a:
- wide transformation
- shuffle-heavy operation

---

# 2. Spark Optimizes Aggressively

Spark:
- fuses operations
- removes unused columns
- performs local reduction before shuffle
- dynamically optimizes execution

---

# 3. Physical Plans Are Distributed Execution Graphs

Spark physical plans should be interpreted as:

```text
distributed execution topology
```

NOT:
- sequential code execution

---

# 4. AQE Dynamically Changes Execution

Modern Spark:
- adapts execution during runtime

based on:
- actual statistics
- shuffle size
- partition distribution

This is a major evolution over traditional static distributed systems.

---

# Mental Model To Remember

```text
Logical Plan
    ↓
Initial Physical Plan
    ↓
Runtime Statistics
    ↓
Adaptive Optimization (AQE)
    ↓
Final Physical Execution Plan
```

This is the real Spark execution lifecycle.

---

# Related Concepts

- Spark Execution Model
- Lazy Evaluation
- Shuffle
- Narrow vs Wide Transformations
- Repartition vs Coalesce
- Adaptive Query Execution (AQE)
- Partitioning
- Catalyst Optimizer
- Spark UI