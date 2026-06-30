# Row vs Column Storage

## Why This Chapter?

In the previous chapter, we saw that Parquet became the de facto storage format for analytical workloads.

However, before understanding Parquet, we first need to understand one of the most important design decisions in analytical storage:

> **Should data be stored row by row or column by column?**

The answer depends entirely on the type of workload.

---

# Two Types of Workloads

Most database workloads fall into one of two categories.

## Transactional (OLTP)

Examples:

- Banking transactions
- Online shopping
- User registration
- Updating customer information

Typical query:

```sql
SELECT *
FROM users
WHERE user_id = 101;
```

Here we want **all information for one user**.

---

## Analytical (OLAP)

Examples:

- Total sales by country
- Average order value
- Most viewed products
- Monthly revenue trends

Typical query:

```sql
SELECT AVG(price)
FROM sales
WHERE country = 'IN';
```

Here we want **one or two columns across millions of rows**.

This difference is the key motivation behind columnar storage.

---

# Row-Oriented Storage

Imagine a table:

| user_id | country | age | salary |
|---------|----------|-----|--------|
| 101 | IN | 25 | 50000 |
| 102 | US | 30 | 70000 |
| 103 | UK | 28 | 60000 |

A row-oriented file stores data like this:

```
101,IN,25,50000
102,US,30,70000
103,UK,28,60000
```

Each row is stored together.

---

## Advantages of Row Storage

Reading a complete record is extremely efficient.

For example:

```sql
SELECT *
FROM users
WHERE user_id = 101;
```

Once the row is located, every column is already stored together.

Very little disk I/O is required.

This makes row-oriented storage ideal for transactional systems.

---

# The Problem

Now consider an analytical query:

```sql
SELECT AVG(salary)
FROM users;
```

We only need one column:

```
salary
```

However, with row-oriented storage, the database must repeatedly read:

```
user_id
country
age
salary
```

for every row.

Even though three of those columns are never used.

Most of the disk I/O is wasted.

---

# Column-Oriented Storage

Instead of storing rows together, column-oriented storage stores each column independently.

The same table becomes:

```
user_id

101
102
103

country

IN
US
UK

age

25
30
28

salary

50000
70000
60000
```

Now our analytical query:

```sql
SELECT AVG(salary)
FROM users;
```

only needs to read:

```
salary
```

The remaining columns are never touched.

This technique is called **column pruning**.

---

# Why This Is Faster

Suppose our table contains twenty columns.

```
customer_id
name
email
phone
address
country
...
salary
...
```

If our query only requires:

```sql
AVG(salary)
```

then nineteen columns can be skipped entirely.

Less data is read from disk.

Less data is transferred over the network.

Less memory is consumed.

Less CPU is required.

For analytical workloads involving billions of rows, these savings are enormous.

---

# Better Compression

Column-oriented storage provides another important advantage.

Consider the country column:

```
IN
IN
IN
IN
IN
IN
US
US
US
UK
```

Since similar values are stored together, compression algorithms become much more effective.

In contrast, row-oriented storage mixes many unrelated values together:

```
101,IN,25,50000
102,US,30,70000
103,UK,28,60000
```

Repeated values are scattered throughout the file, making compression less efficient.

---

# Does This Mean Row Storage Is Bad?

Not at all.

Each storage model is optimized for a different workload.

| Row Storage | Column Storage |
|-------------|----------------|
| Read complete records | Read selected columns |
| OLTP workloads | OLAP workloads |
| Frequent updates | Large analytical scans |
| Point lookups | Aggregations |
| Transaction processing | Business intelligence |

Neither approach is universally better.

Choosing the wrong storage model for the workload leads to poor performance.

---

# What We Learned

Column-oriented storage was invented because analytical queries usually access a small subset of columns across a very large number of rows.

By storing each column independently, analytical systems can:

- Read significantly less data
- Compress data more efficiently
- Reduce disk I/O
- Improve query performance

This simple design decision became the foundation for modern analytical file formats such as Apache Parquet.

---

# What's Next?

Now that we understand why columnar storage is faster for analytics, we are ready to open the black box.

In the next chapter, we will look inside a Parquet file and understand how it stores data using row groups, column chunks, pages, and metadata.