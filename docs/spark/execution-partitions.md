# Concept

Initially, I felt Apache Spark performs everything fully in-memory, unlike MapReduce which relied heavily on HDFS-based disk operations. Because of this, I assumed Spark would not be able to process files larger than the available RAM. However, this assumption was incorrect, and this is where the concept of execution partitions becomes important.

---

# Why It Exists

Modern data workloads often involve datasets ranging from gigabytes to terabytes or even petabytes. It is neither practical nor cost-effective to vertically scale a single machine's RAM to match dataset size.

Spark solves this problem using distributed processing:
- datasets are divided into execution partitions
- partitions become units of parallel work
- workers process partitions independently

This allows Spark to process datasets much larger than the memory capacity of a single machine.

---

# Internal Mental Model

When Spark reads a file, it does not load the entire dataset into memory.

Instead:
- Spark calculates logical execution partitions (input splits)
- these partitions are typically determined using file size and block boundaries
- partition sizing is commonly influenced by Hadoop block size defaults (often ~128MB)

Conceptually, Spark determines:
- start byte offset
- end byte offset

for each partition.

These partitions become units of parallel computation.

The Spark driver schedules tasks against these partitions, and workers execute those tasks independently.

Spark does NOT:
- fully load the file into memory
- physically rewrite partitioned files during initial reads

Execution partitions are therefore logical compute boundaries, not physical storage partitions.

Workers may process multiple partitions in parallel depending on:
- available CPU cores
- executor configuration
- cluster resources

---

# Example

Processing a 9GB CSV file using:
- Spark cluster with 1 worker
- worker memory limited to 2GB

Even though the file size exceeds available memory, Spark can still process the dataset because:
- the file is split into execution partitions
- partitions are processed independently
- only subsets of data are actively processed at a given time

---

# Common Misconceptions

## Misconception 1
Spark requires enough RAM to fully load the input dataset.

Reality:
Spark processes data partition-by-partition and distributes work across executors/workers.

---

## Misconception 2
Execution partitions are the same as data lake/table partitions.

Reality:
- execution partitions are compute-oriented
- data lake/table partitions are storage and query-oriented

Example of storage partitioning:

```text
year=2026/month=05/day=22/