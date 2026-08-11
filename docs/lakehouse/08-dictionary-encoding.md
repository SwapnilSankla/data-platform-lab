# Dictionary Encoding: Replacing Values with References

## Introduction

In the previous chapter, we learned that Parquet stores **encoded values** inside Data Pages rather than storing raw values directly.

This naturally raises an important question.

> **What does Dictionary Encoding actually do?**

Dictionary Encoding is one of the most effective techniques used by Parquet for reducing storage, especially for analytical datasets containing many repeated values.

The idea itself is surprisingly simple.

Instead of repeatedly storing the same values, store each unique value only once and let the data reference those values using small integer identifiers.

---

## The Problem

Consider the following column.

| Row | Country |
|-----:|---------|
| 1 | IN |
| 2 | IN |
| 3 | US |
| 4 | UK |
| 5 | IN |
| 6 | US |
| 7 | IN |

Notice how often the same strings appear.

```
IN
IN
US
UK
IN
US
IN
```

If this column contained millions of rows, the same country names would be written millions of times.

This repetition consumes storage and creates unnecessary work for compression algorithms.

Can we avoid storing the same value repeatedly?

---

## Building a Dictionary

Dictionary Encoding begins by identifying the unique values in the column.

For the previous example, the unique values are

```
IN
US
UK
```

Parquet stores these values exactly once inside the **Dictionary Page**.

```
Dictionary

0 → IN
1 → US
2 → UK
```

Each unique value is assigned a small integer identifier called a **dictionary index**.

---

## Replacing Values with Dictionary Indices

Once the dictionary has been created, the original column no longer needs to store the strings themselves.

Instead,

```
IN
IN
US
UK
IN
US
IN
```

becomes

```
0
0
1
2
0
1
0
```

These integer identifiers are what the Data Pages store.

At this point, the original logical values have not been lost.

They have simply been replaced with references into the dictionary.

---

## Recovering the Original Values

A common concern is whether replacing values with integers loses information.

It does not.

Whenever the reader encounters an identifier, it simply performs a lookup in the Dictionary Page.

```
0

↓

Dictionary

↓

IN
```

```
1

↓

Dictionary

↓

US
```

```
2

↓

Dictionary

↓

UK
```

Dictionary Encoding changes **how values are represented**, not **what values exist**.

After decoding, the reader reconstructs exactly the same logical value stream that was originally written.

---

## How Dictionary Encoding Fits into a Column Chunk

In the previous chapter, we learned that a Column Chunk consists of one optional Dictionary Page followed by one or more Data Pages.

Conceptually, a dictionary-encoded Column Chunk looks like this.

```
Column Chunk
│
├── Dictionary Page
│
│      0 → IN
│      1 → US
│      2 → UK
│
├── Data Page
│
│      0
│      0
│      1
│      2
│
├── Data Page
│
│      0
│      1
│      0
│
└── ...
```

Notice the separation of responsibilities.

- The Dictionary Page stores the actual values.
- The Data Pages store only dictionary indices.

Multiple Data Pages can therefore share the same dictionary.

---

## Does Dictionary Encoding Always Reduce Storage?

Not necessarily.

Dictionary Encoding works well when many values repeat.

For example,

```
IN
IN
US
UK
IN
US
```

contains only three unique values.

However, consider a column containing randomly generated UUIDs.

```
f8d9...

ab13...

7cc1...

91ef...
```

Almost every value is unique.

In this case, Parquet would need to store

- every UUID inside the Dictionary Page, and
- an identifier for every UUID inside the Data Pages.

The dictionary itself becomes almost as large as the original data.

In such situations, Dictionary Encoding provides little or no benefit.

For this reason, Parquet writers may decide to stop using Dictionary Encoding and instead write subsequent Data Pages using **Plain Encoding**.

This decision is made by the writer implementation and is not mandated by the Parquet format itself.

---

## Why Integer Identifiers?

Replacing values with integers does more than reduce storage.

It transforms arbitrary values into a dense sequence of integers.

For example,

```
IN
US
UK
```

becomes

```
0
1
2
```

Integer sequences are much easier to process efficiently than variable-length strings.

More importantly, they become ideal input for additional encoding techniques.

This is why Dictionary Encoding is often only the first step in Parquet's encoding pipeline.

---

## Dictionary Encoding Is a General Storage Technique

Although we are studying Dictionary Encoding in the context of Parquet, the idea is widely used across modern analytical systems.

Examples include:

- Apache ORC
- Apache Arrow Dictionary Arrays
- ClickHouse `LowCardinality` columns
- Pandas `Categorical` data type
- SQL Server Columnstore
- Vertica

Once you recognize Dictionary Encoding, you will begin to see it throughout the world of analytical databases and columnar storage engines.

---

## Key Takeaways

- Dictionary Encoding stores each unique value only once.
- Every unique value is assigned a dictionary index.
- Data Pages store dictionary indices rather than the original values.
- The Dictionary Page stores the actual values shared by all Data Pages within the Column Chunk.
- Dictionary Encoding is most effective for columns containing many repeated values.
- If the dictionary becomes ineffective, writers may fall back to Plain Encoding.
- Dictionary Encoding transforms arbitrary values into compact integer identifiers, making subsequent encoding techniques more effective.

---

## Looking Ahead

Dictionary Encoding replaces repeated values with integer identifiers.

However, the resulting Data Pages may still contain many repeated identifiers.

For example,

```
0
0
0
0
0
1
1
2
2
2
```

Can we compress these repeated integers even further?

The answer is **Run Length Encoding (RLE)**, which is the next stage in Parquet's encoding pipeline.