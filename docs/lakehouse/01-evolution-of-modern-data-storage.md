# Evolution of Modern Data Storage

## Why This Chapter?

Modern data platforms are built by combining multiple technologies.

For example, a Spark job may read data stored as Parquet files from an Apache Iceberg table registered in a Hive Metastore, orchestrated by Airflow, and stored on Amazon S3.

For someone new to the ecosystem, this can be confusing.

Questions naturally arise:

- Why do we need both Parquet and Iceberg?
- Doesn't Parquet already store metadata?
- If Hive already manages tables, why was Iceberg invented?
- Which technology is responsible for what?

These questions cannot be answered by studying each technology in isolation.

Instead, we need to understand how the modern data lake evolved over time.

---

## The Journey

Throughout this section, we will follow the evolution of analytical storage technologies.

```
CSV
    ↓
Parquet
    ↓
Hive Tables
    ↓
Apache Iceberg
```

Each generation solved a different problem introduced by the previous one.

Rather than treating these as competing technologies, we will learn how they complement each other.

---

## Our Learning Philosophy

For every technology, we will answer the same four questions.

### 1. Why was it invented?

What problem did the industry face?

---

### 2. What does it solve?

What responsibilities belong to this technology?

---

### 3. What does it not solve?

What responsibilities belong somewhere else?

Understanding these boundaries is just as important as understanding the technology itself.

---

### 4. Why did the industry move to the next generation?

Every technology has limitations.

Those limitations often become the motivation for the next generation of tools.

---

## A Guiding Principle

One idea will appear repeatedly throughout this journey.

> **Every technology has a primary responsibility.**

For example:

| Technology | Primary Responsibility |
|------------|------------------------|
| CSV | Store tabular data |
| Parquet | Efficiently store analytical data in a file |
| Hive Metastore | Organize files into tables |
| Apache Iceberg | Manage the lifecycle of tables |

Notice that these technologies do not replace one another.

Instead, they build upon one another.

An Iceberg table typically stores its data in Parquet files.

Understanding where one technology ends and the next begins is the key to understanding modern lakehouse architectures.

---

## What's Next?

Our first stop is one of the oldest data storage formats still in use today.

Before we understand why Parquet became the standard for analytical storage, we first need to understand the limitations of storing data in simple row-oriented text files such as CSV.