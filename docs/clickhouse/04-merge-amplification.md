## 4.1 A System That Defies Intuition

Let’s begin with a situation that feels… wrong.

You observe a ClickHouse cluster:

- Ingestion rate: **600 MB/sec**
- Query load: moderate
- CPU usage: not maxed

But your monitoring shows:

- Disk IO: **2.5–3 GB/sec** sustained

---

## 🤔 Pause

Where is the extra IO coming from?

You’re only ingesting 600 MB/sec.

No massive queries.

So why is the system pushing ~3 GB/sec?

---

## 4.2 The First Wrong Answer

Most people say:

> “Maybe queries are scanning a lot.”
> 

You check.

They aren’t.

---

Another guess:

> “Replication traffic?”
> 

Assume for now — single replica.

Still doesn’t explain it.

---

So we’re left with something uncomfortable:

> The system is doing work you didn’t explicitly ask for.
> 

---

## 4.3 Recalling What We Learned

From Chapter 1:

- Data is rewritten during merges

From Chapter 3:

- Smaller parts → more rewrite passes

Now we quantify that.

---

## 4.4 The Concept of Amplification

Let’s define a term:

```
Merge Amplification Factor
```

This represents:

> How many times data is rewritten after initial ingestion.
> 

---

## 4.5 A Thought Experiment

Imagine a single row:

- Written once during insert
- Rewritten 3 times during merges

Total writes:

```
1 (insert) + 3 (merges) = 4 writes
```

---

## 🤔 Pause

If your system ingests 600 MB/sec…

And each byte is rewritten 4 times…

What is total IO?

---

### Answer

```
600 MB/sec × 4 = 2.4 GB/sec
```

That matches your observation.

---

## 4.6 The Equation That Matters

You can now formalize it:

```
Effective IO = Ingestion IO × Amplification Factor
```

---

## 4.7 Why This Is Dangerous

This relationship is not obvious when you build the system.

Because:

- You measure ingestion
- You measure queries
- But amplification is hidden

So your system appears:

- Efficient at small scale
- Unpredictable at large scale

---

## 4.8 Where Amplification Comes From

Let’s unpack the drivers.

---

### 1. Part Size

From Chapter 3:

- Smaller parts → more merge levels
- More merge levels → more rewrites

---

### 2. Partition Fragmentation

If data is spread across many partitions:

- Each partition merges independently
- Fewer parts per partition
- More merge levels

---

### 3. Continuous Ingestion

If new parts keep arriving:

- Merge system never “catches up”
- Lower-level merges dominate
- Higher-level merges delayed

---

### 4. Merge Scheduling Heuristics

ClickHouse prefers:

- Merging similar-sized parts
- Avoiding very large merges

So:

- Small parts get merged frequently
- Large parts may be delayed

---

## 🤔 Pause

If small merges happen more often than large merges:

> What happens to amplification?
> 

---

### Answer

Amplification increases.

Because data gets rewritten multiple times before reaching large size.

---

## 4.9 A Deeper Visualization

Think of data flowing through levels:

```
Insert → L0 → L1 → L2 → L3 → Final
```

Each arrow is a rewrite.

---

### Case A — Small Parts

```
Insert → L0 → L1 → L2 → L3 → L4 → Final
```

Many steps → high amplification

---

### Case B — Larger Parts

```
Insert → L0 → L1 → Final
```

Fewer steps → lower amplification

---

## 4.10 The Non-Linear Trap

Here’s the subtlety:

Amplification is not linear.

If you:

- Reduce part size by 2×

You may:

- Increase merge levels by more than 2×

Which means:

- Amplification grows faster than expected

---

## 4.11 The IO Illusion

At this point, you might think:

> “We just need more IO bandwidth.”
> 

But pause.

---

## 🤔 Question

If you double IO capacity…

But amplification remains the same…

What happens in a few months as data grows?

---

### Answer

You hit the limit again.

Because:

- Amplification is still multiplying your workload

---

## 4.12 Optimization vs Reality

This leads to a crucial distinction.

---

### Stage 1 — Inefficient System

- Small parts
- High amplification
- IO inflated artificially

Fix:

- Increase batch size
- Reduce parts/sec

---

### Stage 2 — Efficient System

- Large parts
- Minimal amplification
- IO reflects actual data movement

At this point:

> You are bound by physical limits.
> 

---

## 4.13 A Concrete Comparison

Let’s compare two systems.

---

### System A

- Ingestion: 600 MB/sec
- Amplification: 5×

```
Effective IO = 3 GB/sec
```

---

### System B

- Ingestion: 600 MB/sec
- Amplification: 2×

```
Effective IO = 1.2 GB/sec
```

---

## 🤔 Pause

Which system is more scalable?

---

### Answer

System B.

Because:

- Lower amplification
- Lower IO pressure
- More headroom

---

## 4.14 The Critical Realization

> You don’t scale ClickHouse by just handling more data.
> 

You scale it by:

> Reducing how many times that data is rewritten.
> 

---

## 4.15 Stress Test

Suppose:

- You increase batch size 10×
- Parts become 10× larger

What happens to:

- Merge levels?
- Amplification?
- IO?

---

### Answer

- Merge levels ↓
- Amplification ↓
- IO ↓

Even though:

- Raw ingestion remains constant

---

## 4.16 The Dangerous Blind Spot

Many teams:

- Monitor ingestion rate
- Monitor query latency

But ignore:

> Amplification
> 

Which is why they say:

> “System suddenly became unstable”
> 

When in reality:

> Amplification quietly increased over time
> 

---

## 4.17 The Deep Mental Model

You can now extend your system equation:

```
Total IO = Ingestion IO × Amplification Factor + Query IO
```

And in many systems:

> Amplification dominates.
> 

---

## 4.18 Closing Insight

If you take one thing from this chapter:

> Merge amplification is the invisible multiplier that turns a manageable system into an IO-bound system.
>