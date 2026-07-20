## 2.1 Two Teams, Same Data, Different Outcomes

Let’s start with a simple setup.

Two teams are building ingestion pipelines into ClickHouse.

Both teams ingest **exactly the same data**:

- Same schema
- Same volume (say, 1 billion rows per day)
- Same query patterns

From a business perspective, these systems are identical.

---

### Team A

They ingest data as it arrives:

- Each event → one insert
- Continuous, real-time writes

---

### Team B

They batch data:

- Buffer events
- Insert in chunks of ~100,000 rows

---

After a few weeks, something strange happens.

---

### Observations

**Team A:**

- Merge backlog increasing
- IO constantly high
- Query latency degrading
- System feels “noisy”

**Team B:**

- Stable IO
- Predictable merges
- Queries still fast

---

## 🤔 Pause Here

Both systems ingest the same number of rows.

So ask yourself:

> Why is one system unstable while the other is healthy?
> 

Take a moment. Don’t rush.

---

## 2.2 The First Instinct (and Why It Fails)

A common explanation is:

> “Maybe Team A has more queries.”
> 

But we already controlled for that.

Another guess:

> “Maybe their data distribution is different.”
> 

Also controlled.

So what’s left?

---

## 2.3 A Subtle Difference

The only difference is:

- **How the data is inserted**

Let’s zoom into that.

---

## 2.4 What Happens on Insert (Revisited Carefully)

From Chapter 1, you know:

- Every insert creates a **part**
- That part is immutable
- Merges later combine parts

Now, let’s connect this to the two teams.

---

### Team A

- 1 row per insert
- → 1 part per insert

If they ingest 1 million rows:

- They create **1 million parts**

---

### Team B

- 100k rows per insert
- → 1 part per insert

For the same 1 million rows:

- They create **10 parts**

---

## 🤔 Pause Again

Same data.

But:

- Team A → 1,000,000 parts
- Team B → 10 parts

What does that imply for merges?

---

## 2.5 The Explosion You Don’t See

Let’s think about merges now.

Merges combine parts.

So if you have:

- 10 parts → a few merges
- 1,000,000 parts → enormous merge work

But the deeper problem is not just count.

---

## 2.6 The Real Metric (This Is Critical)

At this point, most people still think in:

> “rows per second”
> 

ClickHouse doesn’t care about that as much as you think.

The system actually scales with:

```
parts per second
```

---

Let’s define it:

```
parts/sec = inserts/sec × partitions_touched
```

In this scenario:

- Team A → extremely high inserts/sec → very high parts/sec
- Team B → low inserts/sec → low parts/sec

---

## 💡 First Major Insight

> ClickHouse is constrained by how many *parts* you create, not how many rows you insert.
> 

---

## 2.7 Why Parts Are Expensive (Beyond Count)

Let’s go deeper.

Each part is not just “some rows.”

Each part carries:

- Its own primary index
- Its own metadata
- Its own files in storage
- Its own lifecycle in merges

So when you increase parts:

You increase:

- Metadata in memory
- Number of files / objects
- Merge scheduling complexity
- IO operations

---

## 🤔 Pause

If each part is a unit of work:

> What happens when you create too many units of work per second?
> 

---

## 2.8 The System Falls Behind

Let’s connect this to the core equation from Chapter 1:

```
part_creation_rate <= merge_compaction_rate
```

---

### Team A

- part_creation_rate → extremely high
- merge_compaction_rate → limited by IO

So:

```
part_creation_rate > merge_compaction_rate
```

Result:

- Parts accumulate
- Merge backlog grows
- IO increases (more rewrites needed)
- System destabilizes

---

### Team B

- part_creation_rate → low
- merge_compaction_rate → sufficient

So:

```
part_creation_rate <= merge_compaction_rate
```

Result:

- Parts get merged efficiently
- System stays stable

---

## 2.9 The Hidden Non-Linearity

Here’s the subtle but powerful realization:

> Doubling rows does not necessarily double system cost.
> 
> 
> But doubling parts can *explode* system cost.
> 

Because:

- Parts drive merge work
- Merge work drives IO
- IO drives system stability

---

## 2.10 Continuous Ingestion — The Real Trap

Now let’s make this more realistic.

You might say:

> “We don’t insert one row at a time — we have streaming pipelines.”
> 

Fair.

But even in streaming systems:

- Micro-batch size matters
- Insert frequency matters

If your pipeline produces:

- Very frequent small batches

You are effectively recreating Team A’s problem.

---

## 2.11 The Illusion of Real-Time

There’s a trap here.

Engineers often think:

> “Lower latency ingestion is always better.”
> 

So they reduce batch size.

But in ClickHouse:

> Ultra-low latency ingestion can destroy system stability.
> 

Because:

- You increase inserts/sec
- Which increases parts/sec
- Which increases merge pressure

---

## 💡 Second Major Insight

> There is a tradeoff between ingestion latency and system stability.
> 

---

## 2.12 A Deeper Thought Experiment

Imagine two systems:

### System X

- 10M rows/sec
- Batch size = 1M
- → 10 inserts/sec

### System Y

- 1M rows/sec
- Batch size = 1
- → 1M inserts/sec

---

## 🤔 Pause

Which system is more likely to fail?

---

### Answer

System Y — despite lower data volume.

Because:

- Parts/sec is enormous
- Merge system collapses

---

## 2.13 The Real Control Lever

At this point, you can identify the most powerful lever:

> **Batch size**
> 

Not:

- Hardware
- Schema
- Index

But:

> How much data you group per insert
> 

---

## 2.14 Why Increasing Batch Size Works

When you increase batch size:

- Parts/sec ↓
- Merge frequency ↓
- Merge amplification ↓
- IO ↓

You’re not reducing data.

You’re reducing **work units**.

---

## 2.15 Stress the Model Again

Suppose:

- You increase batch size 10×
- Parts/sec drops 10×

What happens?

---

Pause.

---

### Answer

- Merge backlog reduces
- IO reduces
- System stabilizes

Even though:

- Total data remains the same

---

## 2.16 The Bigger Picture

You now have two foundational truths:

From Chapter 1:

> Data is rewritten multiple times
> 

From Chapter 2:

> The number of parts controls how much rewriting happens
> 

---

Combine them:

> Parts control amplification → amplification controls IO → IO controls stability
> 

---

## 2.17 Closing Insight

If you remember only one thing from this chapter:

> ClickHouse does not scale with rows.
> 
> 
> It scales with how intelligently you *batch those rows into parts*.
>