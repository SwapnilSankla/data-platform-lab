## 8.1 A Pager Goes Off

It’s a regular day.

Suddenly, alerts fire:

- Query latency ↑
- Dashboard slow
- Some timeouts

You open metrics:

- CPU ~40%
- Memory fine
- But IO is high

---

At first glance, it’s confusing.

> “CPU is not maxed… so why is the system slow?”
> 

---

## 🤔 Pause

What is your first instinct?

---

## 8.2 The First Mistake

A common reaction:

> “Let’s increase threads / CPU”
> 

Because:

- CPU is underutilized
- More parallelism should help

---

## ❌ Why This Can Backfire

If the system is IO-bound:

- More threads → more concurrent IO
- More contention
- Higher latency per operation

You end up:

> Slowing the system further
> 

---

## 8.3 The Fundamental Question

Before doing anything, you must answer:

> Is the system CPU-bound or IO-bound?
> 

---

## 8.4 How to Think About This

Let’s simplify:

### CPU-bound system

- CPU ~90–100%
- IO moderate
- Threads busy

### IO-bound system

- CPU low/moderate
- IO saturated
- Threads waiting

---

## 💡 Insight

> Low CPU + high latency usually means IO bottleneck.
> 

---

## 8.5 But “IO High” Is Not Enough

Here’s where many engineers stop.

They say:

> “IO is high → that’s the problem”
> 

But that’s incomplete.

You need to ask:

> **Why is IO high?**
> 

---

## 8.6 Two Very Different IO Problems

There are two fundamentally different scenarios.

---

### Case 1 — Amplification Problem

- Many small parts
- High parts/sec
- Merge backlog growing

IO is high because:

> System is rewriting data too many times
> 

---

### Case 2 — Absolute Throughput Problem

- Parts already large
- parts/sec low
- Merge backlog still present

IO is high because:

> System is processing too much data overall
> 

---

## 🤔 Pause

Why is this distinction important?

---

### Answer

Because:

> The fixes are completely different.
> 

---

## 8.7 Real-World Debugging Flow

Now let’s walk through how a expert would debug this.

---

## Step 1 — Look at Parts

Ask:

- How many active parts exist?
- Is the number growing?

---

### Interpretation

- Many small parts → amplification problem
- Few large parts → volume problem

---

## Step 2 — Check Part Sizes

Ask:

- Average part size?

---

### Interpretation

- Very small parts → batching issue
- Healthy sizes (~100MB+) → look elsewhere

---

## Step 3 — Observe Merge Backlog

Ask:

- Are merges lagging behind?

---

### Interpretation

- Yes → merge system overloaded
- No → problem elsewhere (queries?)

---

## Step 4 — Check CPU vs IO

Ask:

- CPU utilization?
- IO throughput?

---

### Interpretation

| CPU | IO | Meaning |
| --- | --- | --- |
| High | Moderate | CPU-bound |
| Low | High | IO-bound |

---

## Step 5 — Correlate with Ingestion

Ask:

- Did ingestion pattern change?
- Smaller batches?
- Higher frequency?

---

### Interpretation

- Yes → parts/sec increased → amplification

---

## Step 6 — Look at Query Patterns

Ask:

- Are queries scanning more data?
- Different filters?

---

### Interpretation

- New queries → scan-heavy → IO increase

---

## 8.8 Putting It Together

You now classify:

---

### Scenario A

- Small parts
- High parts/sec
- Merge backlog

👉 Root cause: **Amplification**

Fix:

- Increase batch size
- Reduce parts/sec

---

### Scenario B

- Large parts
- Low parts/sec
- IO saturated

👉 Root cause: **Absolute volume**

Fix:

- Pre-aggregation
- Reduce data scanned
- Increase IO capacity

---

## 8.9 The Dangerous Misdiagnosis

If you confuse the two:

---

### Treat amplification as volume

You:

- Add hardware
- Increase IO

Result:

- Temporary relief
- Problem returns

---

### Treat volume as amplification

You:

- Increase batch size

Result:

- No meaningful improvement

---

## 8.10 A Real Example

Let’s simulate.

---

### System State

- Parts size: 50k rows
- Parts/sec: high
- IO: 3GB/sec
- CPU: 30%

---

## 🤔 Pause

What is the problem?

---

### Answer

Amplification.

---

### Fix

- Increase batch size
- Reduce parts/sec

---

---

### Another System

- Parts size: 200MB
- Parts/sec: low
- IO: 3GB/sec
- CPU: 30%

---

## 🤔 Pause

Now what?

---

### Answer

Absolute throughput limit.

---

### Fix

- Pre-aggregate
- Reduce data volume

---

## 8.11 Why CPU Can Be Low

This is counterintuitive.

You might think:

> “System is slow → CPU should be high”
> 

But in IO-bound systems:

- Threads wait on IO
- CPU stays idle

---

## 💡 Insight

> Low CPU is often a sign of a blocked system, not an idle one.
> 

---

## 8.12 The Role of Object Storage

In cloud setups:

- IO includes network latency
- Object store throughput limits
- Request overhead

So IO bottlenecks are even more pronounced.

---

## 8.13 The Debugging Mindset

You:

1. Identify bottleneck (CPU vs IO)
2. Identify cause (amplification vs volume)
3. Apply correct lever

---

## 8.14 The Decision Tree

```
Slow system
→ CPU high? → optimize compute
→ CPU low, IO high?
      → small parts? → fix batching
      → large parts? → reduce volume
```

---

## 8.15 Closing Insight

If you remember one thing:

> The hardest part of scaling ClickHouse is not tuning —
> 
> 
> it is correctly identifying whether you are IO-bound due to amplification or absolute data volume.
>