# Data Platform Lab

*A hands-on engineering lab for understanding how modern data platforms actually work — from Spark execution to Iceberg internals and analytical databases.*

Modern data platforms are built from many layers: distributed execution engines, storage formats, metadata systems, analytical databases, and orchestration tools.

This repository documents my journey of understanding these systems from first principles—not by memorizing frameworks, but by uncovering the engineering trade-offs behind them.

---

## Who is this for?

This notebook is intended for engineers who already have some familiarity with modern data tooling and want to understand:

- Why Parquet became the dominant analytical storage format.
- How Spark executes distributed workloads.
- Why Hive breaks at scale.
- How Iceberg solves metadata and consistency problems.
- How analytical databases such as ClickHouse achieve low-latency queries.
- How all these components fit together to form a modern Data Platform.

---

## Prerequisites

This repository deliberately skips introductory material.

There is already excellent documentation explaining:

- What Spark is.
- What Docker and containers are.
- Basic SQL concepts.
- Kafka fundamentals.
- Object storage basics.
- The APIs of individual technologies.

The focus here is different:

> **How do these systems actually work internally, and why were they designed this way?**

To get the most value from these notes, you should already be comfortable with:

- Software engineering fundamentals.
- Linux and containers.
- Basic SQL.
- Distributed systems concepts.
- Reading code and technical documentation.

---

## Recommended Learning Path

The chapters are designed to be followed in order.

### 🧱 Foundations

Build intuition for modern analytical storage:

- Object Storage vs Data Lake vs Lakehouse
- Evolution of Modern Data Storage
- Row vs Column Storage
- Anatomy of a Parquet File
- Row Groups

---

### ⚙️ Spark Internals

Understand how distributed execution actually works:

- Transformations vs Actions
- Lazy Evaluation
- Internal Execution Model
- Execution Partitions
- Narrow vs Wide Transformations
- Shuffle
- Joins
- Physical Plans
- Memory Management

---

### ❄️ Lakehouse & Metadata

Move beyond files and understand table formats:

- Hive Metastore
- Partitioning
- Metadata management
- Apache Iceberg
- Time travel
- Schema evolution

---

### 🚀 ClickHouse

Learn how analytical databases optimize for speed:

- Why columnar databases exist
- Storage engines and parts
- Sparse indexes
- Data skipping
- Merges and compaction
- Materialized views
- Distributed tables
- ClickHouse vs Lakehouse architectures

---

## Philosophy

This repository intentionally focuses on **engineering intuition over framework APIs**.

The goal is not to learn how to call a library.

The goal is to answer questions such as:

- Why does Spark shuffle?
- Why are Parquet row groups important?
- Why do analytical databases sort data?
- Why does Hive struggle with large metadata volumes?
- Why does Iceberg exist?
- How do OLAP engines achieve interactive query performance?

---

## Repository Structure

```text
Fundamentals → Spark → Lakehouse → ClickHouse
                      ↓
              Experiments & Notebooks
```

The emphasis is on building a mental model that connects the entire stack rather than learning each technology in isolation.