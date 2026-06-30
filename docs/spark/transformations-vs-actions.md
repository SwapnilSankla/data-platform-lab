# Transformations vs Actions

## Concept

Apache Spark operations are broadly categorized into:

1. Transformations
2. Actions

Understanding this distinction is fundamental because Spark uses lazy evaluation.

Transformations build execution plans, while actions trigger actual execution.

---

# Why This Concept Exists

Spark is designed as a distributed computation engine.

Instead of executing each operation immediately, Spark first builds an optimized execution plan (DAG).

This enables Spark to:
- Optimize execution
- Reduce unnecessary computation
- Combine operations efficiently
- Minimize data movement
- Generate efficient physical plans

Without lazy evaluation, distributed processing would become significantly less efficient.

---

# Transformations

## Definition

Transformations are operations that define how data should be modified or processed.

Transformations do NOT execute immediately.

Instead, they create a new DataFrame or RDD representing a new logical execution plan.

---

# Internal Mental Model

Suppose we write:

```python
filtered = df.filter("event_type = 'purchase'")

selected = filtered.select("user_id", "product_id")
```

Spark does NOT:
- read the dataset immediately
- filter rows immediately
- select columns immediately

Instead Spark internally builds a logical DAG similar to:

```text
Read CSV
    ↓
Filter purchase events
    ↓
Select required columns
```

This execution plan is called lineage.

No actual computation happens yet.

---

# Characteristics of Transformations

Transformations:
- Are lazily evaluated
- Build lineage/DAG
- Return new DataFrames or RDDs
- Do not materialize results immediately

---

# Common Transformations

| Transformation | Description |
|---|---|
| filter | Filters rows |
| select | Selects columns |
| withColumn | Adds/modifies columns |
| map | Row-level transformation |
| flatMap | Expands rows |
| groupBy | Groups records |
| orderBy | Sorts records |
| repartition | Redistributes partitions |
| coalesce | Reduces partitions |
| join | Combines datasets |

---

# Narrow vs Wide Transformations

Transformations can further be categorized into:

| Type | Requires Shuffle? |
|---|---|
| Narrow Transformation | No |
| Wide Transformation | Yes |

Examples:
- `filter()` → narrow transformation
- `groupBy()` → wide transformation

Wide transformations introduce shuffle and stage boundaries.

---

# Actions

## Definition

Actions trigger actual execution of the DAG.

When an action is called:
- Spark optimizes the plan
- Jobs are created
- Stages are generated
- Tasks are scheduled
- Executors begin computation

This is the moment when lazy evaluation ends.

---

# Internal Mental Model

Suppose we now execute:

```python
selected.count()
```

Spark now:
1. Builds optimized physical plan
2. Creates jobs and stages
3. Launches tasks
4. Reads data
5. Executes transformations
6. Produces final result

Actual computation finally begins.

---

# Characteristics of Actions

Actions:
- Trigger DAG execution
- Materialize results
- Return concrete output
- Start distributed computation

---

# Common Actions

| Action | Description |
|---|---|
| count | Counts records |
| show | Displays rows |
| collect | Brings data to driver |
| write | Persists output |
| take | Returns first N rows |
| first | Returns first row |
| foreach | Executes side effects |
| save | Writes output |

---

# Important Distinction

## Transformations Return Logical Plans

Example:

```python
filtered = df.filter(...)
```

Returns:
- another DataFrame
- another logical execution plan

No computation yet.

---

## Actions Return Materialized Results

Example:

```python
df.count()
```

Returns:
- concrete integer value

Example:

```python
df.write.parquet(...)
```

Produces:
- actual files on storage

---

# Lazy Evaluation

Spark uses lazy evaluation to:
- Combine multiple transformations
- Optimize query plans
- Avoid unnecessary computation
- Minimize shuffle
- Reduce disk and network usage

This is one of Spark's core architectural principles.

---

# Example Workflow

```python
df = spark.read.csv("events.csv")

filtered = df.filter("event_type = 'purchase'")

selected = filtered.select("user_id")

selected.count()
```

Execution behavior:

| Step | Execution? |
|---|---|
| read | No |
| filter | No |
| select | No |
| count | Yes |

Only the action triggers execution.

---

# Catalyst Optimizer

Before execution, Spark uses Catalyst Optimizer to:
- Combine transformations
- Push filters down
- Remove unnecessary columns
- Reorder operations
- Generate optimized physical plans

This optimization happens before actions execute.

---

# Spark UI Observation

Transformations alone usually do not appear in Spark UI because no execution occurs.

Once an action is called:
- Jobs appear
- Stages appear
- Tasks get scheduled
- Shuffle becomes visible

---

# Common Misconceptions

## Misconception 1

Transformations immediately execute.

Reality:
Transformations only build lineage.

---

## Misconception 2

Each transformation creates a separate job.

Reality:
Spark combines transformations into optimized execution plans.

---

## Misconception 3

Transformations are always cheap.

Reality:
Wide transformations may trigger expensive shuffle operations.

---

## Misconception 4

Actions are always safe.

Reality:
Some actions like `collect()` may overload driver memory by bringing large datasets to the driver.

---

# Operational Impact

Understanding transformations vs actions is critical for:
- Debugging Spark jobs
- Avoiding accidental recomputation
- Optimizing performance
- Understanding Spark UI
- Designing scalable pipelines
- Efficient caching strategies

This concept forms the foundation for:
- Lazy evaluation
- DAG execution
- Query optimization
- Caching and persistence

---

# Related Concepts

- Lazy Evaluation
- Jobs, Stages, and Tasks
- Narrow vs Wide Transformations
- Shuffle
- Catalyst Optimizer
- Caching and Persistence
- Execution Plans
- DAG Lineage