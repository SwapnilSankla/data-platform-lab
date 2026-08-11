# Statistics and Predicate Pushdown: Reading Less Data

## Introduction

So far, we have focused on how Parquet stores data efficiently.

- Row Groups enable parallel processing.
- Column Chunks enable column pruning.
- Encodings reduce storage.
- Compression reduces the number of bytes written to disk.

These optimizations make reading data faster.

However, the fastest data to read is the data that **never needs to be read at all**.

This raises an important question.

> **How can a query engine know that an entire Row Group is irrelevant without reading any of its Data Pages?**

The answer lies in **statistics** stored in the Parquet file's metadata.

---

# Two Different Optimizations

Before understanding statistics, it is important to distinguish between two independent optimizations that Parquet provides.

## 1. Column Pruning

Suppose a table contains

| id | country | amount |
|----|----------|---------|

and the query is

```sql
SELECT amount
FROM sales;
```

The query only needs the **amount** column.

Because Parquet stores each column separately inside a Row Group, the reader only loads the **amount Column Chunk**.

```
Row Group

├── Column Chunk (id)
├── Column Chunk (country)
└── Column Chunk (amount)
```

Neither **id** nor **country** is read.

This optimization is called **Column Pruning**.

It is possible because a Row Group is physically organized as one **Column Chunk per column**.

---

## 2. Row Group Pruning

Now consider a different query.

```sql
SELECT amount
FROM sales
WHERE amount > 1000;
```

Suppose the file contains three Row Groups.

| Row Group | amount (Min) | amount (Max) |
|-----------|--------------|--------------|
| RG1 | 10 | 500 |
| RG2 | 600 | 900 |
| RG3 | 950 | 5000 |

The query engine evaluates the predicate

```
amount > 1000
```

against the statistics.

```
RG1

Max = 500

↓

Cannot satisfy predicate

↓

Skip
```

Likewise,

```
RG2

Max = 900

↓

Skip
```

Only RG3 might contain matching rows.

```
RG3

Max = 5000

↓

Read
```

This optimization is called **Row Group Pruning**.

Notice something subtle.

The **decision** is to skip an entire Row Group.

The **information used to make that decision** comes from the statistics stored for the **amount Column Chunk** inside that Row Group.

---

# The Same Structure Enables Two Optimizations

The physical organization of a Row Group enables both optimizations.

```
Row Group
│
├── Column Chunk (id)
│
├── Column Chunk (country)
│
└── Column Chunk (amount)
```

Because each column has its own Column Chunk,

- queries can read only the required columns (**Column Pruning**).

Because every Column Chunk has associated metadata,

- queries can decide whether an entire Row Group can be skipped (**Row Group Pruning**).

The same physical structure therefore enables two completely different performance optimizations.

---

# Where Are Statistics Stored?

Up to this point, we have treated statistics as though they belong to a Column Chunk.

Conceptually, this is a useful way to think about them.

```
Row Group
│
├── Column Chunk
│     ├── Statistics
│     ├── Dictionary Page
│     └── Data Pages
```

This diagram expresses **ownership**.

The statistics describe that Column Chunk.

However, it is **not** the physical layout of a Parquet file.

---

# Physical Layout

Physically, the Data Region contains only the bytes required to reconstruct values.

The metadata describing those bytes lives separately in the **Parquet footer**.

```
Parquet File

+--------------------------------------+
|                                      |
| Data Region                          |
|                                      |
|  Row Group                           |
|      ├── Column Chunk                |
|      │     ├── Dictionary Page       |
|      │     └── Data Pages            |
|      │                               |
|      ├── Column Chunk                |
|      └── Column Chunk                |
|                                      |
+--------------------------------------+

+--------------------------------------+
| File Metadata (Footer)               |
|                                      |
|  Row Group Metadata                  |
|      ├── Column Chunk Metadata       |
|      │      ├── Statistics           |
|      │      ├── Compression Codec    |
|      │      ├── Encodings            |
|      │      ├── Dictionary Offset    |
|      │      └── Data Page Offset     |
|      │                               |
|      └── ...                         |
+--------------------------------------+
```

The footer stores **metadata about each Column Chunk**, including where its bytes are located in the Data Region.

---

# How a Reader Uses Statistics

When opening a Parquet file, a reader first locates the footer.

```
Read last 8 bytes

↓

Locate File Metadata

↓

Read Row Group Metadata
```

For each Row Group, it then reads the metadata for the required Column Chunk.

For example, if the query filters on

```sql
WHERE amount > 1000
```

the reader only examines the metadata for the **amount Column Chunk**.

```
Column Chunk Metadata

↓

Min Value

↓

Max Value

↓

Predicate Evaluation
```

If the statistics prove that the predicate cannot be satisfied,

```
Skip Row Group
```

No Dictionary Pages are read.

No Data Pages are read.

No decompression occurs.

If the Row Group might satisfy the predicate, the reader uses the stored byte offsets to jump directly to the required Column Chunk.

---

# Statistics Eliminate Impossibilities

Statistics can prove that a Row Group **cannot** satisfy a predicate.

They cannot prove that it **does**.

Suppose

```
Min = 10

Max = 100
```

Now consider

```sql
WHERE amount = 75
```

Since 75 lies between 10 and 100, the Row Group **might** contain a matching value.

The query engine must read it.

It is entirely possible that no row actually contains 75.

Statistics therefore eliminate impossible candidates rather than guaranteeing matches.

---

# Why This Design Matters

Separating metadata from data has several important advantages.

- Readers evaluate predicates by reading only the footer.
- Entire Row Groups can be skipped without touching the Data Region.
- The footer provides precise byte offsets for every Column Chunk.
- Readers seek directly to the required bytes instead of scanning the file.

The Data Region stores values.

The Footer stores everything required to locate, interpret, and optimize access to those values.

---

# The Bigger Picture

We have now seen that different physical structures in Parquet enable different optimizations.

| Physical Structure | Enables | Why |
|--------------------|---------|-----|
| Row Group | Parallelism | Independent units of work that can be processed concurrently. |
| Column Chunk | Column Pruning | Each column is stored separately. |
| Column Chunk Metadata | Row Group Pruning | Statistics determine whether an entire Row Group can be skipped. |
| Data Pages | Efficient I/O | Only the required pages are read and decompressed. |

Rather than viewing these as independent design choices, they work together to minimize the amount of data that must be read during query execution.

---

# Statistics Are the Foundation of Modern Lakehouses

The idea of using metadata to avoid unnecessary reads extends beyond Parquet.

Parquet uses metadata to determine

> "Can I skip this Row Group?"

Apache Iceberg applies the same principle at a higher level.

Instead of Row Groups, Iceberg asks

> "Can I skip this entire data file?"

It answers that question using metadata stored in manifest files.

Understanding Parquet statistics therefore provides the conceptual foundation for understanding how Iceberg performs efficient query planning.

---

# Key Takeaways

- A Row Group is the unit of pruning.
- Column Chunk statistics provide the information needed to decide whether a Row Group can be skipped.
- Column Pruning and Row Group Pruning are two independent optimizations enabled by the same physical organization of a Row Group.
- Statistics logically belong to a Column Chunk but are physically stored in the Parquet footer.
- The footer stores metadata and byte offsets that allow readers to seek directly to the required Column Chunks.
- Separating metadata from data is one of Parquet's fundamental design principles and is a recurring design pattern in modern lakehouse architectures.

---

# Looking Ahead

We now understand how Parquet stores data efficiently, how it minimizes storage, and how it avoids reading unnecessary data.

However, production data lakes rarely contain a single Parquet file.

Instead, they contain millions of Parquet files distributed across object storage.

Managing those files efficiently is the responsibility of the **table format**, not the **file format**.

In the next section, we begin our deep dive into **Apache Iceberg**, where we will see how the same principles of metadata-driven query planning scale from individual Row Groups to entire collections of Parquet files.