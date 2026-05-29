# Spark Internal Execution Model

# Why This Matters

Apache Spark may initially appear like a simple distributed data processing framework, however internally Spark is a distributed execution engine composed of multiple cooperating runtime components.

Understanding these components is critical because:
- distributed execution behavior becomes easier to reason about
- Spark UI becomes meaningful
- debugging becomes significantly easier
- performance tuning becomes intuitive instead of trial-and-error

---

# High Level Architecture

```text
Spark Application
        │
        ▼
     Driver
        │
        ▼
     Master
        │
        ▼
     Workers
        │
        ▼
    Executors
        │
        ▼
      Tasks
```

---

# Core Runtime Components

## Driver

Driver is the most important Spark process.

Driver acts as:
- application coordinator
- DAG scheduler
- execution planner

Responsibilities:
- runs the Spark application
- creates SparkSession/SparkContext
- builds execution DAG
- converts DAG into stages and tasks
- schedules tasks on executors
- monitors execution progress
- handles retries/failures

The driver is effectively the "brain" of the Spark application.

---

## Master

Master is the cluster resource coordinator.

Responsibilities:
- tracks available workers
- tracks cluster resources
- manages worker registration
- allocates executors
- monitors worker health

Master does NOT:
- execute tasks
- process data
- build DAGs

Master only coordinates cluster-level resource management.

---

## Worker

Worker is a node-level resource manager.

Responsibilities:
- registers with master
- advertises available CPU/memory
- launches executor JVMs
- monitors executor lifecycle

Workers themselves do NOT process data directly.

Actual data processing happens inside executors.

---

## Executor

Executors are the actual distributed compute processes.

Responsibilities:
- execute tasks
- process partitions
- perform shuffles
- cache data
- report execution status back to driver

Executors are where actual distributed computation happens.

---

# Execution Model

Spark internally converts application logic into distributed execution units.

The hierarchy looks like:

```text
Action
  ↓
Job
  ↓
Stages
  ↓
Tasks
```

---

# Jobs

Jobs are triggered by:
- Spark actions

Examples:
- count()
- show()
- collect()
- write()

A job represents a complete distributed execution request.

---

# Stages

Jobs are divided into stages.

Stages are created around:
- shuffle boundaries

A shuffle occurs when Spark must redistribute data across partitions/executors.

Examples causing shuffle:
- groupBy()
- join()
- distinct()
- orderBy()

Stages generally execute sequentially because downstream stages depend on outputs from previous stages.

---

# Tasks

Stages are further divided into tasks.

Tasks are:
- smallest execution unit in Spark
- executed in parallel
- typically mapped roughly one-per-partition

Tasks run inside executors.

Concurrency is generally limited by:
- available executor cores

Example:

```text
2 executor cores
→ roughly 2 concurrent tasks
```

---

# Shuffle

Shuffle is one of the most important Spark concepts.

Shuffle means:

```text
redistribution of data across partitions/executors
```

Shuffle usually involves:
- network transfer
- disk spill
- repartitioning
- sorting

Shuffle is expensive because it introduces:
- network IO
- serialization/deserialization
- synchronization barriers

Many Spark optimizations focus on reducing shuffle operations.

---

# Lazy Evaluation

Spark uses lazy evaluation.

Transformations are NOT executed immediately.

Instead:
- Spark builds logical execution lineage
- execution starts only when an action is triggered

Example:

```python
df.filter(...).groupBy(...)

# no execution yet
```

Execution begins only when an action appears:

```python
df.count()
```

---

# Catalyst Optimizer vs Tungsten

These are different internal Spark optimization systems.

---

## Catalyst Optimizer

Catalyst handles:
- logical query optimization

Examples:
- predicate pushdown
- projection pruning
- query rewriting

Catalyst optimizes:
- what should execute

---

## Tungsten

Tungsten handles:
- low-level execution optimization

Examples:
- binary memory format
- whole-stage code generation
- reduced JVM object overhead
- cache-aware execution

Tungsten optimizes:
- how execution happens

---

# Spark UI Mapping

Spark UI visualizes this execution hierarchy.

## Jobs Tab
Shows:
- actions
- jobs
- duration

---

## Stages Tab
Shows:
- stages
- shuffle boundaries
- stage DAGs
- task counts

---

## Tasks
Shows:
- partition-level execution
- retries
- failures
- execution timing

---

## Executors
Shows:
- executor memory
- task distribution
- shuffle metrics

---

# Important Mental Model

Spark is best understood as:

```text
a lazy distributed DAG scheduler
operating on partitioned data
through executors
coordinated by the driver
using cluster resources managed by master/workers
```

---

# End-to-End Execution Example

Consider the following PySpark code:

```python
df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "false")
    .csv("s3a://clickstream/2019-Nov.csv")
)

df.count()
```

This simple-looking operation triggers several distributed execution steps internally.

---

# Step 1 — Lazy Transformation Definition

The CSV read operation itself does NOT immediately execute.

Spark only builds:
- logical execution lineage
- metadata about transformations

No actual computation happens yet.

---

# Step 2 — Action Triggers Execution

```python
df.count()
```

is an action.

Actions trigger:
- job creation
- DAG generation
- stage planning
- task scheduling

Spark now starts actual distributed execution.

---

# Step 3 — Input Partitioning

Spark divides the large CSV file into execution/input partitions.

Example:

```text
9GB CSV
→ ~68 execution partitions
```

These are logical execution splits, not physical file copies.

Spark workers process these partitions incrementally.

This allows Spark to process datasets much larger than available RAM.

---

# Step 4 — Partition-Level Parallel Processing

Spark schedules tasks across executors.

Conceptually:

```text
Partition 1 → partial count
Partition 2 → partial count
...
Partition 68 → partial count
```

Each task processes:
- one execution partition
- independently
- in parallel

Concurrency depends on:
- available executor cores

---

# Step 5 — Partial Aggregation

Spark first performs local aggregation within each partition.

Instead of shuffling the entire dataset, Spark computes:

```text
local partition counts
```

This dramatically reduces:
- network traffic
- shuffle size
- memory overhead

This optimization pattern is extremely common in distributed systems.

---

# Step 6 — Shuffle / Exchange

Spark now needs to produce:
- one final scalar count value

To achieve this:
- partial counts from partitions are redistributed
- final aggregation stage is created

Spark SQL/DataFrame UI may show this as:

```text
Exchange
ShuffleExchange
SinglePartition
```

Importantly:

Spark is NOT shuffling the entire CSV dataset.

It is only shuffling:
- small partial aggregate outputs

Example:

```text
68 partitions
→ 68 partial count values
→ final aggregation
```

---

# Step 7 — Final Aggregation

Spark performs final reduce aggregation:

```text
sum(partial_counts)
```

This produces:
- final count result

---

# Execution Hierarchy For This Example

```text
count() Action
    ↓
1 Job
    ↓
Multiple Stages
    ↓
~68 Tasks
```

Tasks execute:
- partition-level work
- inside executors
- in parallel

Stages execute sequentially due to:
- shuffle dependencies

---

# Spark UI Observations

This example demonstrates several Spark UI concepts.

## Jobs Tab
Shows:
- count() action execution

---

## Stages Tab
Shows:
- CSV scan stage
- aggregation stage
- shuffle boundary

---

## Tasks
Shows:
- one task per execution partition
- task execution timing
- retries/failures

---

## SQL/DataFrame Tab
Shows:
- physical execution plan
- scan operations
- exchanges/shuffles
- aggregation operators

---

# Important Learning

This example demonstrates that Spark is fundamentally:

```text
a distributed DAG execution engine
operating on partitioned data
using parallel tasks
with staged execution boundaries around shuffles
```

The DataFrame API appears simple, but Spark internally performs sophisticated distributed execution planning and optimization.

---

# Related Concepts

- Execution Partitions
- Transformations vs Actions
- Shuffle Operations
- Spark Memory Model
- Catalyst Optimizer
- Tungsten Engine
- Lazy Evaluation
- Fault Tolerance
- Spark History Server