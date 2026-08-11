# Bit Packing: Eliminating Wasted Bits

## Introduction

In the previous chapter, we learned that Run Length Encoding (RLE) efficiently stores long sequences of repeated values.

For example,

```
0
0
0
0
0
```

becomes

```
(0,5)
```

However, not every sequence contains repeated values.

Consider the following dictionary indices.

```
0
1
2
3
0
2
1
3
```

Every value is different.

Run Length Encoding offers little benefit.

Yet storing each value using a full 32-bit integer would still waste a significant amount of space.

This is where **Bit Packing** becomes useful.

---

## The Problem

Suppose Dictionary Encoding has produced the following identifiers.

```
0
1
2
3
```

There are only four possible values.

How many bits are actually required to represent them?

| Value | Binary |
|-------:|--------|
| 0 | 00 |
| 1 | 01 |
| 2 | 10 |
| 3 | 11 |

Only **2 bits** are required.

If we stored these values using ordinary 32-bit integers, we would waste 30 bits for every value.

```
00000000000000000000000000000000

00000000000000000000000000000001

00000000000000000000000000000010

00000000000000000000000000000011
```

Almost every bit carries no useful information.

---

## The Core Idea

Bit Packing stores values using only the number of bits actually required.

Instead of

```
32 bits
32 bits
32 bits
32 bits
```

Bit Packing stores

```
2 bits
2 bits
2 bits
2 bits
```

The values become

```
00 01 10 11
```

packed tightly together without unused bits.

Conceptually,

```
00|01|10|11
```

occupies only 8 bits instead of 128 bits.

---

## Determining the Bit Width

The number of bits required depends on the largest value in the sequence.

For example,

| Largest Value | Required Bits |
|---------------:|--------------:|
| 1 | 1 |
| 3 | 2 |
| 7 | 3 |
| 15 | 4 |
| 255 | 8 |

Parquet computes the minimum bit width capable of representing every dictionary identifier in the current sequence.

Smaller dictionaries therefore require fewer bits.

---

## Why Dictionary Encoding Comes First

Dictionary Encoding transforms arbitrary values into a dense sequence of integers.

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

These identifiers occupy a very small range.

Since Bit Packing only cares about the largest value, dictionary indices become excellent candidates for bit packing.

Without Dictionary Encoding, Bit Packing would have to operate on arbitrary values such as strings or large integers, which is generally not practical.

Dictionary Encoding and Bit Packing therefore naturally complement each other.

---

## Bit Packing Is Also Reversible

Like every Parquet encoding, Bit Packing is completely reversible.

During reading, the Parquet reader knows the bit width used for the packed values.

It simply extracts the required number of bits for each value and reconstructs the original sequence of dictionary identifiers.

```
Packed Bits

↓

Dictionary IDs

↓

Dictionary Lookup

↓

Logical Values
```

The original logical values are recovered exactly.

---

## How Bit Packing Fits into the Hybrid Encoding

The Parquet specification defines an **RLE / Bit-Packing Hybrid** encoding.

Rather than choosing one encoding for an entire page, the encoded stream consists of a sequence of runs.

Each run is either

- an RLE run, or
- a Bit-Packed run.

For example,

```
Encoded Stream

↓

RLE Run
0 repeated 100 times

↓

Bit-Packed Run
0 1 2 3 1 0 2 3

↓

RLE Run
2 repeated 40 times

↓

Bit-Packed Run
1 3 0 2 1 0 3 2
```

This hybrid design allows Parquet to efficiently represent both highly repetitive data and rapidly changing values within the same Data Page.

---

## Key Takeaways

- Bit Packing reduces storage by eliminating unused bits.
- The number of bits required depends on the largest value being represented.
- Dictionary Encoding naturally produces compact integer identifiers that are ideal for Bit Packing.
- Bit Packing is completely reversible.
- Parquet combines Run Length Encoding and Bit Packing into a single hybrid encoding, allowing each run of values to be stored using whichever representation is more efficient.

---

## Looking Ahead

We now understand the three core encoding techniques used throughout Parquet.

- Dictionary Encoding eliminates repeated values.
- Run Length Encoding eliminates repeated patterns.
- Bit Packing eliminates wasted bits.

The next question is equally important.

How does a Parquet reader know **which encoding** was used for each Data Page and reconstruct the original values correctly?

To answer that, we need to look at **Page Headers and Page Metadata**, the information that tells every reader how to interpret the bytes stored inside a Data Page.