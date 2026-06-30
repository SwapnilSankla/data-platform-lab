# Row Groups — The Unit of Parallelism in a Parquet File

## Why This Chapter?

In the previous chapter, we learned that a Parquet file consists of two major sections:

* Data (one or more Row Groups)
* Footer (metadata)

This naturally raises the next question:

> **Why does Parquet divide data into Row Groups instead of storing one giant block of columnar data?**

Understanding Row Groups is one of the most important steps toward understanding how Spark efficiently processes Parquet files and, later, why Apache Iceberg builds upon Parquet rather than replacing it.

---

# Imagine a Parquet File Without Row Groups

Suppose we have a Parquet file containing one billion rows.

Without Row Groups, the file would conceptually look like this:

```
+---------------------------------------------+
|                                             |
|           One Huge Column Store             |
|                                             |
+---------------------------------------------+
```

Although the data is stored column by column, it still behaves like one enormous unit.

Now imagine Spark needs to execute:

```sql
SELECT *
FROM events
WHERE event_date = '2026-06-01'
```

Several problems immediately appear:

* Can multiple executors independently process different regions of the file?
* Can Spark skip only part of the file?
* Can metadata describe different portions of the data separately?

The answer is essentially **no**.

The file is simply too coarse-grained.

---

# Enter Row Groups

Parquet solves this by dividing the data into **Row Groups**.

Conceptually, the file now looks like:

```
+---------------------------------------------+
| Row Group 1                                 |
+---------------------------------------------+
| Row Group 2                                 |
+---------------------------------------------+
| Row Group 3                                 |
+---------------------------------------------+
| Row Group 4                                 |
+---------------------------------------------+
| Footer                                      |
+---------------------------------------------+
```

Each Row Group contains a subset of the rows.

For example:

| Row Group | Rows                  |
| --------- | --------------------- |
| RG1       | 1 – 1,000,000         |
| RG2       | 1,000,001 – 2,000,000 |
| RG3       | 2,000,001 – 3,000,000 |
| RG4       | 3,000,001 – 4,000,000 |

Notice something important.

The rows remain in their original order.

Parquet is **not partitioning or shuffling the data**.

It is simply breaking the file into independently readable regions.

---

# Why Are Row Groups So Important?

A Row Group is much more than a chunk of rows.

It is the **smallest independently readable unit** within a Parquet file.

Each Row Group has its own:

* Column data
* Compression
* Encodings
* Statistics (minimum, maximum, null count)
* Metadata

This means every Row Group can be processed independently.

---

# Row Groups Enable Parallel Processing

Suppose a Parquet file contains four Row Groups.

```
+-------------+
| Row Group 1 |
+-------------+
| Row Group 2 |
+-------------+
| Row Group 3 |
+-------------+
| Row Group 4 |
+-------------+
```

Spark can assign them independently.

```
Executor A  ---> Row Group 1

Executor B  ---> Row Group 2

Executor C  ---> Row Group 3

Executor D  ---> Row Group 4
```

Instead of one executor reading an enormous file, multiple executors can process different Row Groups simultaneously.

This is one of the reasons Parquet scales so well for analytical workloads.

---

# Row Groups Also Enable Data Skipping

Suppose each Row Group stores statistics for the `event_date` column.

| Row Group | Min Date   | Max Date   |
| --------- | ---------- | ---------- |
| RG1       | 2026-01-01 | 2026-01-31 |
| RG2       | 2026-02-01 | 2026-02-28 |
| RG3       | 2026-03-01 | 2026-03-31 |

Now consider the query:

```sql
SELECT *
FROM events
WHERE event_date = '2026-02-15'
```

Spark first reads the Parquet footer.

It immediately discovers:

* RG1 cannot contain February data.
* RG3 cannot contain February data.

Only RG2 needs to be read.

The remaining Row Groups are skipped entirely.

No disk I/O.

No decompression.

No CPU spent processing irrelevant data.

This optimization is known as **Row Group pruning**, and it is one of the reasons Parquet performs so well for analytical queries.

---

# Why Data Organization Matters

Notice something interesting.

The effectiveness of Row Group pruning depends heavily on how the data is written.

Imagine two files.

### Randomly Ordered Data

Every Row Group contains records from every month.

```
RG1
Jan
Feb
Mar

RG2
Jan
Feb
Mar
```

Every Row Group has similar statistics.

Spark cannot skip much.

---

### Chronologically Ordered Data

```
RG1
January

RG2
February

RG3
March
```

Now each Row Group represents a distinct time range.

Spark can eliminate entire Row Groups simply by inspecting the metadata.

The physical organization of the data dramatically influences query performance.

Parquet does **not** automatically sort data before writing.

However, when data is naturally clustered or intentionally sorted on frequently filtered columns, Row Group pruning becomes much more effective.

---

# Connecting Row Groups Back to Spark

Earlier, during our Spark deep dive, we learned how Spark creates tasks to process data in parallel.

When reading Parquet files, Spark does **not** simply divide the file into arbitrary byte ranges.

Instead, Spark plans work around Row Groups.

Conceptually:

```
Parquet File
      │
      ▼
+-------------+
| Row Group 1 |
+-------------+
| Row Group 2 |
+-------------+
| Row Group 3 |
+-------------+
```

Spark can assign one or more Row Groups to each task.

This preserves the integrity of the Parquet format while allowing efficient parallel execution.

---

# Row Groups in the Bigger Picture

At this point, we have uncovered several important building blocks of Parquet:

* The footer stores file-level metadata.
* The footer describes every Row Group.
* Every Row Group stores its own statistics.
* Spark reads the footer first to decide which Row Groups should be scanned.
* Well-organized Row Groups can dramatically reduce the amount of data read during a query.

These ideas will become even more important when we study Apache Iceberg.

Iceberg extends this same principle beyond individual Parquet files by maintaining metadata across thousands of Parquet files, allowing entire files—not just Row Groups—to be skipped during query execution.

---

# What's Next?

We now understand **why** Row Groups exist.

The next question is:

> **How is a Row Group internally organized?**

We'll discover that a Row Group is itself divided into **Column Chunks**, which are the building blocks that make columnar storage and efficient compression possible.
