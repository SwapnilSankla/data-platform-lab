# Partition Size != Actual Runtime Memory Usage

## Concept

Initially, it may seem intuitive that if a Spark execution partition is roughly 128MB and the executor has 2GB RAM, then processing should always succeed comfortably.

However, this assumption is incorrect because:
- partition size represents input data size on disk
- runtime memory usage represents fully materialized in-memory execution state

These two numbers can differ significantly.

---

## Why This Happens

Spark does not process raw bytes directly from disk.

During execution:
- CSV/text data gets parsed
- rows become JVM objects
- strings get allocated
- execution metadata gets created
- serialization/deserialization buffers are allocated
- shuffle and aggregation buffers may appear

As a result:
- in-memory representation often becomes much larger than on-disk size

---

## Example

Suppose a CSV partition is:

```text
128MB on disk
```

During processing, Spark may allocate memory for:
- parsed rows
- Java/Python objects
- UTF string representations
- InternalRow structures
- task execution buffers
- S3/network buffers
- JVM overhead

Actual memory consumption may therefore become:
- several hundred MB
- or even multiple GB in extreme cases

depending on workload complexity.

---

## CSV Is Especially Expensive

CSV is:
- row-oriented
- text-based
- schema-less at storage level

Spark must:
- parse text
- infer/cast types
- allocate strings
- deserialize rows

This creates substantial CPU and memory overhead.

This is one major reason modern analytical systems prefer:
- Parquet
- ORC
- Iceberg-backed tables
- Delta Lake

which use:
- binary formats
- columnar storage
- typed encoding

---

## Spark Memory Is Shared Across Multiple Concerns

Executor memory is not used only for partition data.

It is also consumed by:
- JVM heap
- execution memory
- shuffle buffers
- aggregation state
- serialization/deserialization
- task metadata
- Python worker processes
- network buffers
- filesystem connector buffers

This means even relatively small partitions can trigger memory pressure.

---

## Parallelism Multiplies Memory Usage

If an executor runs multiple tasks concurrently:

```text
2 cores → 2 simultaneous tasks
```

then memory usage increases accordingly.

Example:

```text
128MB partition × 2 concurrent tasks
```

does NOT imply only:

```text
256MB memory usage
```

because runtime overhead also multiplies.

---

## Schema Inference Is Expensive

CSV schema inference may:
- scan data multiple times
- sample rows aggressively
- allocate parsing structures

This increases:
- IO
- CPU
- memory pressure

In production systems, explicit schemas are generally preferred.

---

## PySpark Adds Additional Overhead

PySpark execution involves:
- JVM executors
- Python worker processes

Data often crosses:

```text
JVM ↔ Python boundary
```

through serialization/deserialization.

This introduces:
- additional memory overhead
- extra CPU cost
- buffer allocations

---

## Operational Impact

Spark memory tuning is influenced by:
- file format
- partition sizing
- task concurrency
- shuffle behavior
- serialization overhead
- execution engine internals

This means:
- executor sizing is a workload-specific tuning exercise
- raw file size alone is not enough to estimate memory requirements

---

## Most Important Learning

Execution partition size should NOT be interpreted as:

```text
actual runtime memory usage
```

Distributed compute systems operate on:
- parsed
- deserialized
- materialized
- transformed

data structures whose runtime footprint may greatly exceed original storage size.

---

## Related Concepts

- Execution Partitions
- Lazy Evaluation
- Transformations vs Actions
- Shuffle Operations
- Executor Sizing
- Spark Memory Model
- Parquet vs CSV
- JVM Object Overhead
- PySpark Serialization
- Narrow vs Wide Transformations