# Run Length Encoding (RLE): Compressing Repeated Patterns

## Introduction

In the previous chapter, we learned that Dictionary Encoding replaces repeated values with compact integer identifiers.

For example,

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

This representation is already smaller than storing repeated strings.

However, notice something interesting.

The integer identifiers themselves often repeat.

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

Do we really need to store every repeated identifier individually?

Run Length Encoding answers this question.

---

## The Core Idea

Run Length Encoding (RLE) stores repeated values as a single value together with the number of consecutive times it appears.

Instead of writing

```
0
0
0
0
0
```

RLE stores

```
(0,5)
```

meaning

> "The value 0 appears five consecutive times."

Likewise,

```
1
1
```

becomes

```
(1,2)
```

and

```
2
2
2
```

becomes

```
(2,3)
```

The encoded representation becomes

```
(0,5)
(1,2)
(2,3)
```

---

## Decoding Is Straightforward

Decoding simply performs the reverse operation.

```
(0,5)
```

expands back into

```
0
0
0
0
0
```

Likewise,

```
(2,3)
```

becomes

```
2
2
2
```

No information is lost.

RLE changes only the physical representation of the data.

---

## Why RLE Works So Well After Dictionary Encoding

Dictionary Encoding transforms arbitrary values into small integers.

```
California
California
California
Texas
Texas
Ohio
```

becomes

```
0
0
0
1
1
2
```

Now RLE can immediately identify repeated runs.

```
0
0
0
```

↓

```
(0,3)
```

Without Dictionary Encoding, RLE would need to repeatedly store long strings.

Small integer identifiers make RLE significantly more effective.

This is why Dictionary Encoding and RLE are often used together.

---

## When Does RLE Work Well?

RLE performs well when identical values appear consecutively.

For example,

```
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

compresses extremely well.

On the other hand,

```
0
1
0
2
1
0
2
```

contains almost no consecutive repetition.

In this case, RLE provides little benefit because nearly every value begins a new run.

The effectiveness of RLE therefore depends on the ordering of values within the column.

---

## RLE Is an Encoding, Not Compression

Although RLE reduces storage, Parquet treats it as an **encoding**, not as a compression algorithm.

The storage pipeline therefore becomes

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
Run Length Encoding
        │
        ▼
Compression
        │
        ▼
Bytes on Disk
```

Notice that compression still happens after RLE.

This distinction is important because encoding changes the representation of the data, while compression reduces the size of the resulting byte stream.

---

## A Small but Important Detail

The Parquet specification does not use a standalone RLE encoding.

Instead, it defines an **RLE / Bit-Packing Hybrid** encoding.

Why combine them?

Imagine the following sequence.

```
0
0
0
0
0
```

RLE is extremely efficient.

Now consider

```
0
1
2
3
4
5
```

Every value is different.

RLE would perform poorly because every run has length one.

In these situations, Bit Packing is more efficient.

The hybrid encoding allows Parquet to choose the most appropriate representation for different portions of the data.

We will study Bit Packing in the next chapter.

---

## Key Takeaways

- Run Length Encoding stores repeated values as **(value, count)** pairs.
- RLE is completely reversible.
- RLE works best when identical values occur consecutively.
- Dictionary Encoding naturally creates integer sequences that are ideal input for RLE.
- In Parquet, RLE is an encoding stage rather than a compression algorithm.
- Parquet actually uses an **RLE / Bit-Packing Hybrid** encoding to efficiently handle both repeated and non-repeated values.

---

## Looking Ahead

Run Length Encoding efficiently stores repeated values.

But what happens when every value is different?

For example,

```
0
1
2
3
4
5
6
```

There are no runs to compress.

Even so, each value still occupies more bits than necessary.

The next chapter explores **Bit Packing**, a technique that reduces storage by eliminating wasted bits rather than repeated values.# Run Length Encoding (RLE): Compressing Repeated Patterns

## Introduction

In the previous chapter, we learned that Dictionary Encoding replaces repeated values with compact integer identifiers.

For example,

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

This representation is already smaller than storing repeated strings.

However, notice something interesting.

The integer identifiers themselves often repeat.

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

Do we really need to store every repeated identifier individually?

Run Length Encoding answers this question.

---

## The Core Idea

Run Length Encoding (RLE) stores repeated values as a single value together with the number of consecutive times it appears.

Instead of writing

```
0
0
0
0
0
```

RLE stores

```
(0,5)
```

meaning

> "The value 0 appears five consecutive times."

Likewise,

```
1
1
```

becomes

```
(1,2)
```

and

```
2
2
2
```

becomes

```
(2,3)
```

The encoded representation becomes

```
(0,5)
(1,2)
(2,3)
```

---

## Decoding Is Straightforward

Decoding simply performs the reverse operation.

```
(0,5)
```

expands back into

```
0
0
0
0
0
```

Likewise,

```
(2,3)
```

becomes

```
2
2
2
```

No information is lost.

RLE changes only the physical representation of the data.

---

## Why RLE Works So Well After Dictionary Encoding

Dictionary Encoding transforms arbitrary values into small integers.

```
California
California
California
Texas
Texas
Ohio
```

becomes

```
0
0
0
1
1
2
```

Now RLE can immediately identify repeated runs.

```
0
0
0
```

↓

```
(0,3)
```

Without Dictionary Encoding, RLE would need to repeatedly store long strings.

Small integer identifiers make RLE significantly more effective.

This is why Dictionary Encoding and RLE are often used together.

---

## When Does RLE Work Well?

RLE performs well when identical values appear consecutively.

For example,

```
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

compresses extremely well.

On the other hand,

```
0
1
0
2
1
0
2
```

contains almost no consecutive repetition.

In this case, RLE provides little benefit because nearly every value begins a new run.

The effectiveness of RLE therefore depends on the ordering of values within the column.

---

## RLE Is an Encoding, Not Compression

Although RLE reduces storage, Parquet treats it as an **encoding**, not as a compression algorithm.

The storage pipeline therefore becomes

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
Run Length Encoding
        │
        ▼
Compression
        │
        ▼
Bytes on Disk
```

Notice that compression still happens after RLE.

This distinction is important because encoding changes the representation of the data, while compression reduces the size of the resulting byte stream.

---

## A Small but Important Detail

The Parquet specification does not use a standalone RLE encoding.

Instead, it defines an **RLE / Bit-Packing Hybrid** encoding.

Why combine them?

Imagine the following sequence.

```
0
0
0
0
0
```

RLE is extremely efficient.

Now consider

```
0
1
2
3
4
5
```

Every value is different.

RLE would perform poorly because every run has length one.

In these situations, Bit Packing is more efficient.

The hybrid encoding allows Parquet to choose the most appropriate representation for different portions of the data.

We will study Bit Packing in the next chapter.

---

## Key Takeaways

- Run Length Encoding stores repeated values as **(value, count)** pairs.
- RLE is completely reversible.
- RLE works best when identical values occur consecutively.
- Dictionary Encoding naturally creates integer sequences that are ideal input for RLE.
- In Parquet, RLE is an encoding stage rather than a compression algorithm.
- Parquet actually uses an **RLE / Bit-Packing Hybrid** encoding to efficiently handle both repeated and non-repeated values.

---

## Looking Ahead

Run Length Encoding efficiently stores repeated values.

But what happens when every value is different?

For example,

```
0
1
2
3
4
5
6
```

There are no runs to compress.

Even so, each value still occupies more bits than necessary.

The next chapter explores **Bit Packing**, a technique that reduces storage by eliminating wasted bits rather than repeated values.