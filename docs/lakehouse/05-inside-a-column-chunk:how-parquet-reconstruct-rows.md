# How Parquet Reconstructs Rows

## Introduction

In the previous chapter, we learned that a **Row Group** consists of one **Column Chunk** for every column in the table.

This naturally raises an important question.

If Parquet stores each column independently, and each column may use different encodings and compression techniques, **how does it reconstruct the original rows?**

Consider the following table.

| Row | user_id | country |
|-----:|--------:|----------|
| 1 | 101 | IN |
| 2 | 102 | IN |
| 3 | 103 | US |
| 4 | 104 | US |
| 5 | 105 | UK |

Since Parquet is a columnar format, the values belonging to a single row are physically separated across different column chunks.

```
Row 1

user_id = 101
country = IN
```

becomes

```
Column Chunk (user_id)

101
102
103
104
105
```

```
Column Chunk (country)

IN
IN
US
US
UK
```

Yet when Spark reads the file, it successfully reconstructs the original rows.

How?

The answer lies in understanding the difference between the **logical representation** and the **physical representation** of data.

---

## A Column Chunk Represents a Logical Value Stream

It is tempting to think of a column chunk as simply a collection of bytes containing column values.

This is not entirely correct.

Conceptually, a column chunk represents a **logical stream of values** belonging to a single column.

For the previous example, the logical representation is simply:

**user_id**

```
101
102
103
104
105
```

**country**

```
IN
IN
US
US
UK
```

Notice an important property.

- Every column contains exactly the same number of logical values.
- The values appear in row order.
- There are no explicit row identifiers connecting values across columns.

Instead, the position of a value within each logical stream implicitly represents its row.

| Logical Position | user_id | country |
|-----------------:|--------:|----------|
| 1 | 101 | IN |
| 2 | 102 | IN |
| 3 | 103 | US |
| 4 | 104 | US |
| 5 | 105 | UK |

As long as every column produces values in the same logical order, rows can always be reconstructed.

---

## Logical Representation vs Physical Representation

The logical representation describes **what the data means**.

The physical representation describes **how the data is stored on disk**.

These are not the same thing.

For example, the logical country column is

```
IN
IN
US
US
UK
```

Parquet may choose to store this using **Dictionary Encoding**.

Dictionary

```
0 → IN
1 → US
2 → UK
```

Indices

```
0
0
1
1
2
```

Or it may choose **Run Length Encoding (RLE)**.

```
(IN, 2)

(US, 2)

(UK, 1)
```

Although these physical representations look completely different, they both represent the exact same logical sequence of values.

This distinction is one of the most important concepts in understanding Parquet.

---

## The Role of the Parquet Reader

Spark never reads encoded bytes directly.

Instead, the Parquet reader is responsible for transforming the physical representation back into a logical value stream.

Conceptually, the process looks like this.

```
Encoded Bytes

↓

Parquet Decoder

↓

Logical Values

↓

Spark
```

Regardless of whether the data was dictionary encoded, run-length encoded, or compressed, the decoder always produces the same logical values.

For Dictionary Encoding

```
Dictionary

↓

Indices

↓

IN
IN
US
US
UK
```

For Run Length Encoding

```
(IN,2)
(US,2)
(UK,1)

↓

IN
IN
US
US
UK
```

Spark is completely unaware of the encoding used on disk.

It only receives a stream of logical values.

---

## How Rows Are Reconstructed

A common misconception is that Parquet stores hidden row pointers describing which values belong together.

It does not.

Instead, imagine that every requested column has its own decoder.

```
user_id Decoder

↓

101
102
103
104
105
```

```
country Decoder

↓

IN
IN
US
US
UK
```

Each decoder behaves like an iterator.

Every time Spark requests the next value, each decoder advances by one logical position.

Conceptually:

```
userId = userIdDecoder.next()

country = countryDecoder.next()

Row(userId, country)
```

The process repeats until the entire row group has been read.

Rows are therefore **not stored explicitly**.

They are reconstructed dynamically by consuming synchronized logical value streams from multiple column decoders.

---

## Why Encodings Do Not Break Row Reconstruction

At first glance, dictionary encoding and RLE appear to destroy the original sequence of values.

For example, this logical stream

```
IN
IN
US
US
UK
```

may become

```
Dictionary

0 → IN
1 → US
2 → UK

Indices

0
0
1
1
2
```

or

```
(IN,2)

(US,2)

(UK,1)
```

However, these encodings only change **how the values are stored**.

They do **not** change the logical sequence of values produced by the decoder.

Before Spark ever receives data, the Parquet reader decodes these physical representations back into the original logical value stream.

As a result, every decoder still emits:

```
Logical Value #1

Logical Value #2

Logical Value #3

...
```

Because every requested column emits values in the same logical order, Spark can reconstruct rows without requiring explicit row identifiers or row pointers.

---

## Key Takeaways

- A column chunk represents a **logical stream of values**, not a collection of rows.
- The logical representation of data is independent of its physical representation on disk.
- Dictionary Encoding, Run Length Encoding, and other compression techniques only change the physical storage format.
- The Parquet reader decodes encoded bytes back into logical values before Spark processes them.
- Rows are reconstructed by consuming synchronized logical value streams from multiple column decoders.
- No explicit row pointers are required because every column emits values in the same logical order.

---

## Looking Ahead

Throughout this chapter, we treated the Parquet decoder as a black box.

We now understand **what** it produces—a stream of logical values—but not **how** it performs the decoding.

In the next chapter, we will open a **Column Chunk** and explore its internal building blocks, including **Dictionary Pages**, **Data Pages**, and the encoding techniques that make Parquet both compact and efficient.