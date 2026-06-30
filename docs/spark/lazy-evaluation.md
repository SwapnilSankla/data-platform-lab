# Lazy Evaluation in Apache Spark

# Why This Matters

One of Spark's most important design principles is:

```text
lazy evaluation
```

Understanding lazy evaluation is critical because it explains:
- why transformations do not execute immediately
- why Spark can optimize execution plans
- why actions trigger jobs
- how Spark reduces unnecessary computation
- how DAGs are built internally

Without understanding lazy evaluation, Spark execution often appears "magical".

---

# What Is Lazy Evaluation?

Spark does NOT execute transformations immediately.

Instead:
- Spark records transformations
- builds logical execution lineage
- delays execution until an action is triggered

Conceptually:

```python
df = spark.read.csv(...)

filtered = df.filter(...)

grouped = filtered.groupBy(...)

# still no execution
```

Spark only builds:
- metadata
- execution lineage
- logical DAG

No distributed computation happens yet.

---

# What Triggers Execution?

Execution begins only when an action is called.

Examples of actions:
- count()
- show()
- collect()
- write()
- save()

Example:

```python
grouped.count()
```

Now Spark:
- creates job(s)
- builds stages
- schedules tasks
- starts distributed execution

---

# Mental Model

Spark behaves more like:

```text
query planner
```

than:
- immediate execution engine

Conceptually:

```text
Transformations
    ↓
Logical Plan Construction
    ↓
Optimization
    ↓
Action Trigger
    ↓
Physical Execution
```

---

# Why Spark Uses Lazy Evaluation

Lazy evaluation enables Spark to:
- optimize execution plans
- reduce unnecessary computation
- combine transformations efficiently
- minimize data movement
- eliminate redundant operations

This is one major reason Spark can scale efficiently.

---

# Example

Consider:

```python
df = spark.read.csv("s3a://clickstream/2019-Nov.csv")

result = (
    df.filter(df.event_type == "purchase")
      .select("product_id", "price")
      .groupBy("product_id")
      .avg("price")
)

# no execution yet
```

Even though multiple transformations were defined:
- Spark has NOT yet read the CSV fully
- no tasks have started
- no workers are processing data

Spark is only building:
- logical execution lineage

Execution begins only after:

```python
result.count()
```

---

# DAG Construction

During lazy evaluation, Spark internally builds a DAG.

DAG stands for:

```text
Directed Acyclic Graph
```

The DAG represents:
- transformations
- dependencies
- execution relationships

Example:

```text
CSV Scan
   ↓
Filter
   ↓
Select
   ↓
GroupBy
   ↓
Aggregation
```

Spark later converts this DAG into:
- stages
- tasks
- physical execution plans

---

# Transformations vs Actions

Lazy evaluation exists because Spark distinguishes between:
- transformations
- actions

---

## Transformations

Transformations:
- define computation
- remain lazy
- return new DataFrames/RDDs

Examples:
- filter()
- select()
- map()
- groupBy()
- repartition()

Transformations alone do NOT trigger execution.

---

## Actions

Actions:
- require actual results
- trigger distributed execution

Examples:
- count()
- collect()
- show()
- write()

Actions cause Spark to:
- materialize execution
- launch jobs
- execute tasks

---

# Catalyst Optimization

Because Spark delays execution, it can optimize the entire query plan before running it.

Spark's Catalyst Optimizer may:
- push filters closer to data source
- remove unused columns
- combine operations
- optimize joins
- reduce shuffles

This optimization is possible because:
- Spark sees the full execution plan before execution starts

---

# Example of Optimization

Suppose:

```python
df.select("product_id").filter(df.price > 100)
```

Spark may internally reorder operations for efficiency.

Instead of:
- reading all columns first

Spark may:
- filter early
- read fewer columns

This reduces:
- IO
- memory usage
- network traffic

---

# Physical Execution Happens Later

Only after an action:
- logical plan becomes physical plan
- stages are created
- tasks are scheduled
- executors begin computation

This is why Spark UI usually remains empty until:
- an action executes

---

# Important Operational Observation

A common beginner misconception is:

```text
Spark transformations execute immediately
```

They do not.

Example:

```python
df.filter(...)

print("done")
```

The filter operation may not have executed at all yet.

Spark only recorded the transformation.

---

# Another Important Consequence

Because transformations are lazy:
- Spark can avoid unnecessary computation

Example:

```python
df.filter(...).select(...)
```

If no action ever uses this DataFrame:
- Spark performs no execution

This avoids wasted work.

---

# Lazy Evaluation and Fault Tolerance

Spark lineage created during lazy evaluation also supports:
- recomputation
- fault tolerance

If a partition is lost:
- Spark can reconstruct it
- by replaying transformations from lineage

This is one reason Spark does not always require:
- immediate materialization

---

# Spark UI Relationship

Lazy evaluation explains why:
- jobs appear only after actions
- stages/tasks do not exist immediately
- execution DAG appears after triggering execution

Example:

```python
df.count()
```

may create:
- jobs
- stages
- tasks
- shuffle boundaries

even though earlier transformations appeared instantaneous.

---

# Important Mental Model

Spark is best understood as:

```text
a lazy distributed query planner
that converts transformations into optimized distributed execution
only when results are required
```

---

# Related Concepts

- Transformations vs Actions
- DAG Execution
- Catalyst Optimizer
- Jobs, Stages, Tasks
- Narrow vs Wide Transformations
- Shuffle Operations
- Spark SQL Physical Plans
- Fault Tolerance
- Lineage