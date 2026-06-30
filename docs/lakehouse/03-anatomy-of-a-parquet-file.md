# Anatomy of a Parquet File

## Why This Chapter?

In the previous chapter, we learned **why** column-oriented storage is well suited for analytical workloads.

Now it's time to look inside a Parquet file.

Although a Parquet file appears as a single binary file on disk, it has a carefully designed internal structure that allows query engines like Spark to efficiently locate metadata and read only the data they need.

This chapter focuses on one question:

> **How is a Parquet file physically organized?**

---

# Conceptual Structure

At the highest level, every Parquet file consists of two logical parts.

```
+----------------------------------+
|                                  |
|             Data                 |
|                                  |
|        (Multiple Row Groups)     |
|                                  |
+----------------------------------+
|                                  |
|             Footer               |
|                                  |
+----------------------------------+
```

The **Data** section stores the actual records.

The **Footer** stores metadata describing how to interpret the data.

Notice that a Parquet file knows nothing about tables, partitions, snapshots, or transactions.

Its responsibility is simply to store one dataset efficiently.

---

# Physical Layout

Internally, the binary file is organized slightly differently.

```
+----------------------------------+
| Magic Bytes ("PAR1")             |
+----------------------------------+
|                                  |
| Data (Row Groups)                |
|                                  |
+----------------------------------+
| File Metadata (Footer)           |
+----------------------------------+
| Footer Length                    |
+----------------------------------+
| Magic Bytes ("PAR1")             |
+----------------------------------+
```

Let's briefly understand each component.

---

# Magic Bytes

Every Parquet file begins and ends with the four-byte signature:

```
PAR1
```

These magic bytes allow readers to quickly verify that the file is indeed a valid Parquet file.

Think of them as the file's signature.

---

# Data Section

The majority of the file contains the actual data.

Rather than storing all rows together, the data is divided into multiple **Row Groups**.

Each Row Group stores a subset of the dataset.

We intentionally won't dive deeper into Row Groups yet—they deserve an entire chapter of their own.

For now, simply remember that the data section consists of one or more Row Groups.

---

# File Metadata (Footer)

The footer is the most important part of a Parquet file.

It describes everything needed to read the data.

Typical metadata includes:

- Schema
- Number of Row Groups
- Compression codec
- Encoding used
- Statistics
- Location (offset) of every Row Group
- Number of rows

Notice the scope of this metadata.

It describes **one Parquet file**, not an entire table.

This distinction becomes important later when we study Hive and Apache Iceberg.

---

# Footer Length

Immediately before the closing magic bytes, Parquet stores the size of the footer.

```
+----------------------+
| Footer Metadata      |
+----------------------+
| Footer Length = 2048 |
+----------------------+
| PAR1                 |
+----------------------+
```

This small integer tells the reader exactly how many bytes to move backwards in order to locate the footer.

Without it, the reader would have to scan the entire file looking for metadata.

---

# Why Is the Footer at the End?

This is one of Parquet's most elegant design decisions.

Imagine writing a new Parquet file.

Initially, the writer doesn't know:

- How many Row Groups will be created.
- How large each Row Group will be.
- What statistics each Row Group will contain.
- Where each Row Group will be located within the file.

All of this information becomes available **only after the data has been written**.

Therefore, Parquet follows this sequence:

1. Write the data.
2. Collect metadata while writing.
3. Write the footer.
4. Record the footer length.
5. Write the closing magic bytes.

This allows the metadata to accurately describe the completed file.

---

# How Spark Reads a Parquet File

When Spark opens a Parquet file, it does **not** start by reading the data.

Instead, it works backwards.

```
Read last 4 bytes
        ↓
Verify "PAR1"
        ↓
Read footer length
        ↓
Jump directly to footer
        ↓
Read metadata
        ↓
Decide which Row Groups to read
```

This is why Spark can make intelligent decisions before scanning the data itself.

For example, Spark can determine:

- the schema,
- the number of Row Groups,
- available statistics,
- and the compression algorithm

without reading the entire file.

---

# What We Learned

A Parquet file is more than a compressed binary blob.

It has a carefully designed layout consisting of:

- A data section containing one or more Row Groups.
- A footer describing how to interpret that data.
- Magic bytes and a footer length that allow readers to quickly locate the metadata.

This layout enables engines like Spark to inspect metadata first and read only the data required by a query.

---

# What's Next?

Now that we understand the overall layout of a Parquet file, we are ready to study one of its most important building blocks:

> **Row Groups**

We'll answer questions such as:

- What exactly is a Row Group?
- Why do Row Groups exist?
- Why are they the unit of parallelism?
- How do they enable efficient analytical queries?