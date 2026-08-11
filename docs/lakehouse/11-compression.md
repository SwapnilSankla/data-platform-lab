# Compression: Turning Encoded Data into Compact Bytes

## Introduction

In the previous chapters, we learned how Parquet transforms logical values into increasingly compact representations.

A typical write pipeline now looks like this.

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
RLE / Bit Packing
        │
        ▼
?
```

Although the data has already become much smaller, there is still an opportunity to reduce its storage footprint even further.

This is where **compression** comes in.

Unlike encoding, which changes how values are represented, compression reduces the size of the encoded byte stream before it is written to disk.

---

## Encoding vs Compression

Encoding and compression are often confused because both reduce storage size.

However, they solve different problems.

| Encoding | Compression |
|----------|-------------|
| Changes the physical representation of data | Reduces the size of the byte stream |
| Aware of the logical structure of the data | Operates on bytes without understanding their meaning |
| Examples: Dictionary Encoding, RLE, Bit Packing | Examples: Snappy, ZSTD, Gzip, LZ4 |
| Happens before compression | Happens after encoding |

Encoding prepares the data.

Compression makes the prepared data even smaller.

---

## Why Compression Happens After Encoding

Suppose a column contains

```
IN
IN
IN
IN
US
US
```

Dictionary Encoding transforms it into

```
0
0
0
0
1
1
```

Run Length Encoding further transforms it into

```
(0,4)
(1,2)
```

Notice how much more regular the data has become.

Compression algorithms perform best when the input contains repeated patterns and predictable byte sequences.

By encoding the data first, Parquet gives the compression algorithm a much easier problem to solve.

Conceptually, the storage pipeline becomes

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
Compressed Bytes
```

Encoding and compression therefore complement each other rather than compete with each other.

---

## What Gets Compressed?

A common misconception is that an entire Parquet file is compressed as one large block.

It is not.

Compression is applied **independently to each page**.

Conceptually,

```
Parquet File
│
└── Row Group
     │
     └── Column Chunk
          │
          ├── Dictionary Page (Compressed)
          ├── Data Page       (Compressed)
          ├── Data Page       (Compressed)
          └── Data Page       (Compressed)
```

Each page can be decompressed independently.

This design is important because analytical queries rarely need every page in every column.

Instead, a query engine decompresses only the pages that it actually reads.

---

## Why Compress Pages Independently?

Imagine a Parquet file containing one hundred Data Pages.

A query may need only three of those pages.

If the entire file were compressed as a single block, the reader would first have to decompress the entire file before accessing those three pages.

By compressing pages independently, Parquet allows readers to decompress only the pages that are actually required.

This significantly reduces CPU usage and improves query performance.

---

## Common Compression Codecs

Parquet supports several compression codecs.

Each represents a trade-off between storage size and CPU cost.

| Codec | Compression Ratio | Compression Speed | Decompression Speed | Typical Use Case |
|--------|-------------------|-------------------|---------------------|------------------|
| Snappy | Medium | Very Fast | Very Fast | General-purpose analytics |
| ZSTD | High | Fast | Fast | Modern analytical workloads |
| Gzip | Very High | Slow | Slow | Archival storage |
| LZ4 | Lower | Extremely Fast | Extremely Fast | Low-latency workloads |

There is no universally "best" codec.

The appropriate choice depends on the workload.

---

## Why Isn't the Highest Compression Always Best?

It is tempting to think that smaller files always produce faster queries.

In practice, this is not always true.

A highly compressed file may reduce storage space and network traffic, but it also requires more CPU time to decompress.

Analytical systems often prioritize **query performance** over achieving the smallest possible file size.

For this reason, many systems use **Snappy** by default because it provides an excellent balance between compression ratio and decompression speed.

Modern data platforms are increasingly adopting **ZSTD**, which often achieves significantly better compression while maintaining excellent decompression performance.

Choosing a compression codec is therefore an engineering trade-off between

- Storage cost
- Network bandwidth
- CPU utilization
- Query latency

---

## Compression Is Independent of Iceberg

Compression is a property of the **Parquet file**, not the **Iceberg table**.

Iceberg manages metadata such as

- snapshots,
- manifests,
- schema evolution,
- partition evolution,

but it does not define how the underlying Parquet pages are compressed.

Whether a Parquet file uses Snappy, ZSTD, or Gzip, Iceberg's metadata remains exactly the same.

This separation of responsibilities is one of the key design principles of the Lakehouse architecture.

---

## Key Takeaways

- Compression is applied after encoding.
- Encoding transforms values; compression reduces the resulting byte stream.
- Parquet compresses pages independently rather than compressing the entire file.
- Independent page compression enables efficient random access during query execution.
- Different compression codecs represent different trade-offs between storage efficiency and CPU cost.
- Compression is a property of the Parquet file and is independent of Iceberg.

---

## Looking Ahead

At this point, we understand how Parquet stores data efficiently.

However, storing data efficiently is only half the story.

The real power of Parquet comes from **avoiding unnecessary reads altogether**.

How does a query engine know that an entire Row Group can be skipped without reading a single Data Page?

The answer lies in **statistics**, one of the most important optimizations in modern analytical storage engines and a fundamental building block for understanding how Apache Iceberg performs query pruning.