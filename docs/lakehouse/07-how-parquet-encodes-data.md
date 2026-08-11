# How Parquet Encodes Data

## Introduction

In the previous chapter, we opened a **Column Chunk** and discovered that it is internally organized into **Dictionary Pages** and **Data Pages**.

We also learned that Data Pages do not store raw values directly. Instead, they store **encoded values**.

This naturally raises the next question.

> **What does it mean to encode data?**

More importantly,

> **How can Parquet reduce storage without changing the original data?**

This chapter answers these questions by introducing the concept of **encoding** and explaining how it fits into Parquet's storage pipeline.

---

## Encoding Is Not Compression

One of the most common misconceptions is treating **encoding** and **compression** as the same thing.

They are not.

Although both reduce storage size, they solve different problems.

An **encoding** transforms logical values into a different physical representation that is more storage efficient while preserving the original information.

A **compression algorithm** then compresses those encoded bytes to reduce the number of bytes written to disk.

Conceptually, the write path looks like this.

```
Logical Values
        │
        ▼
Encoding
        │
        ▼
Encoded Values
        │
        ▼
Compression
        │
        ▼
Bytes Written to Disk
```

Reading a Parquet file performs the exact reverse.

```
Bytes on Disk
        │
        ▼
Decompression
        │
        ▼
Encoded Values
        │
        ▼
Decoding
        │
        ▼
Logical Values
```

Encoding changes **how values are represented**.

Compression changes **how those bytes are stored**.

These are two separate stages in the storage pipeline.

---

## What Is an Encoding?

An encoding is a **reversible transformation** that converts logical values into a more storage-efficient physical representation.

The word **reversible** is important.

Regardless of how values are represented on disk, a Parquet reader must always reconstruct the exact same logical values.

For example, the logical values

```
IN
IN
US
UK
IN
```

may be represented very differently on disk.

However, after decoding, the reader must always produce

```
IN
IN
US
UK
IN
```

without losing or changing any information.

---

## Why Encode Before Compressing?

At first glance, it may seem that compression alone should be sufficient.

However, compression algorithms work best when the input data already exhibits predictable patterns.

Encoding helps create those patterns.

Consider the following logical values.

```
IN
IN
IN
US
US
UK
```

Rather than repeatedly storing the strings themselves, an encoding may first transform them into

```
0
0
0
1
1
2
```

This representation is already much smaller than repeatedly storing string values.

Additional encodings may further simplify this representation before it is finally compressed.

By the time compression is applied, the data is significantly more compact than the original logical values.

Encoding and compression therefore complement each other rather than compete with each other.

---

## Encodings Work Together

A common misconception is thinking that Parquet chooses one encoding from a list.

```
Dictionary Encoding

OR

Run Length Encoding

OR

Plain Encoding
```

In reality, multiple encodings often work together.

For example, a typical storage pipeline may look like this.

```
Logical Values
        │
        ▼
Dictionary Encoding
        │
        ▼
Dictionary IDs
        │
        ▼
Run Length Encoding /
Bit-Packing Hybrid
        │
        ▼
Compression
        │
        ▼
Bytes on Disk
```

Each stage performs a different transformation.

- Dictionary Encoding replaces repeated values with integer identifiers.
- Run Length Encoding compresses repeated identifiers.
- Compression algorithms further reduce the resulting byte stream.

Understanding this layered design is essential for understanding Parquet.

---

## Where Are These Encodings Stored?

In the previous chapter we learned that a Column Chunk consists of one optional **Dictionary Page** followed by one or more **Data Pages**.

```
Column Chunk
│
├── Dictionary Page
│
├── Data Page
├── Data Page
└── Data Page
```

The Dictionary Page stores the unique values for the column.

The Data Pages store encoded representations of those values.

Interestingly, the **Dictionary Page itself is stored using Plain Encoding**, while the Data Pages typically store encoded dictionary identifiers.

This separation allows multiple Data Pages to share the same dictionary.

---

## Does Every Column Use Dictionary Encoding?

No.

Parquet supports several encoding techniques, including:

- Plain Encoding
- Dictionary Encoding
- Run Length Encoding / Bit-Packing Hybrid
- Delta Encodings
- Byte Stream Split

The Parquet format defines these encodings, but it does **not** require writers to use a particular one.

Instead, the writer decides which encoding is most appropriate for a column.

For example, if a column contains many repeated values, dictionary encoding is usually effective.

If the number of distinct values becomes too large, the writer may decide to store subsequent pages using Plain Encoding instead.

This is a writer implementation decision rather than a requirement of the Parquet format.

---

## Key Takeaways

- Encoding and compression are two different stages in Parquet's storage pipeline.
- Encoding transforms logical values into a more storage-efficient physical representation.
- Compression reduces the size of the encoded byte stream.
- Multiple encodings often work together rather than replacing one another.
- Dictionary Pages store unique values, while Data Pages store encoded representations of those values.
- The Parquet format defines several encodings, but the writer chooses which encoding to use.

---

## Looking Ahead

We now understand where encoding fits into Parquet's storage pipeline.

The next question is far more interesting.

**How does Dictionary Encoding actually work?**

In the next chapter, we will build a Dictionary Page from scratch, see how Data Pages reference it, and understand why Dictionary Encoding is one of the biggest reasons Parquet achieves such high compression ratios for analytical workloads.