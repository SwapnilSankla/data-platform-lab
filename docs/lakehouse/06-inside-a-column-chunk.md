# Inside a Column Chunk

## Introduction

In the previous chapters, we explored the structure of a Parquet file from the file level down to **Row Groups** and learned how rows are reconstructed from independently stored columns.

So far, however, we have treated a **Column Chunk** as a black box.

This chapter opens that black box.

Rather than focusing on how values are encoded, our goal is to understand **how a Column Chunk is organized internally** and the role each component plays.

Before diving in, it is useful to understand the primary responsibility of each storage abstraction in the Parquet format.

| Abstraction | Primary Responsibility |
|--------------|------------------------|
| **File / Row Group** | Parallelization |
| **Column Chunk** | Efficient Column I/O |
| **Data Page** | Encodings & Compression |

This classification comes directly from the Parquet specification and provides a useful mental model for understanding the rest of the format.

---

## Recap

At this point we understand the following hierarchy.

```
Parquet File
    │
    ▼
Footer
    │
    ▼
Row Group
    │
    ▼
Column Chunk
```

A Row Group contains one Column Chunk for every column in the table.

When Spark executes a query such as

```sql
SELECT country
FROM users
```

the footer allows Spark to locate the **country** Column Chunk directly without reading the remaining columns.

A Column Chunk therefore serves as the unit of **column-oriented I/O**, allowing analytical engines to read only the columns required by a query.

Until now, however, we have treated the Column Chunk as a single continuous block of data.

It is not.

---

## Opening the Column Chunk

Internally, a Column Chunk is organized as a sequence of pages.

Conceptually, it looks like this.

```
Column Chunk
│
├── Dictionary Page (optional)
│
├── Data Page
├── Data Page
├── Data Page
└── Data Page
```

A Column Chunk may contain:

- Zero or one Dictionary Page.
- One or more Data Pages.

This organization is defined by the Parquet format specification.

---

## Dictionary Page

A Dictionary Page stores a lookup table containing the unique values for a column.

For example, consider the following logical values.

```
IN
IN
US
UK
IN
US
```

Rather than storing the strings repeatedly, the Dictionary Page stores

```
0 → IN
1 → US
2 → UK
```

The Data Pages then reference these dictionary entries using integer identifiers.

A Column Chunk can contain **at most one Dictionary Page**, and when present, it always appears before the first Data Page.

This allows readers to load the dictionary before decoding any encoded values.

---

## Data Pages

The actual column values are stored inside Data Pages.

A Column Chunk typically contains many Data Pages.

```
Column Chunk
│
├── Dictionary Page
│
├── Data Page
├── Data Page
├── Data Page
└── Data Page
```

Each Data Page contains:

- Encoded values
- A page header describing how those values are stored
- Optional compression

Unlike the Dictionary Page, every Data Page is independent and carries the metadata required to interpret its encoded contents.

---

## Why Divide a Column Chunk into Pages?

At first glance, it may seem simpler to store an entire Column Chunk as one continuous encoded stream.

Instead, Parquet divides every Column Chunk into multiple Data Pages.

Pages serve as the organizational unit where Parquet applies:

- Encoding
- Compression
- Page-specific metadata

This organization has several important consequences.

- Encoding strategies can change from one page to another if required.
- Compression is applied independently to each page.
- Readers decode one page at a time rather than treating the entire Column Chunk as a single encoded stream.
- Each page has its own metadata describing how its contents should be interpreted.

Notice that these are properties of the storage format itself rather than implementation details of a particular query engine.

---

## What We Have Not Covered Yet

Although we now understand the internal organization of a Column Chunk, one important question remains unanswered.

A Data Page contains **encoded values**.

But what do those encoded values actually look like?

How can repeated strings, integers, booleans, or timestamps be represented efficiently while still allowing the original logical values to be reconstructed?

Answering these questions requires understanding the encoding techniques used by Parquet.

That is the focus of the next chapter.

---

## Key Takeaways

- A Column Chunk is **not** a single block of encoded data.
- Internally, it is organized into Pages.
- A Column Chunk contains at most one Dictionary Page and one or more Data Pages.
- The Dictionary Page stores unique values shared across the entire Column Chunk.
- Data Pages store the encoded column values together with the metadata required to decode them.
- Column Chunks are the unit of efficient column-oriented I/O, while Data Pages are the unit where encodings and compression are applied.