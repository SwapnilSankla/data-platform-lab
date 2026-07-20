## 1.1 A System That Should Have Worked

Imagine you’ve just built a data platform.

Nothing fancy — but not small either.

- Events flowing in at a few million per second
- ClickHouse cluster sitting behind ingestion
- Queries running dashboards, aggregations, reports

For the first few weeks, everything feels… effortless.

- Ingestion is smooth
- Queries are fast
- CPU utilization is modest
- Storage is growing, but predictably

You feel confident.

---

Then, slowly, something starts to change.

Not dramatically. Not suddenly. But enough to make you uneasy.

- IO starts creeping up
- Some queries feel slower
- Background tasks seem more active
- Disk and network graphs look noisier

You scale the cluster slightly. Things improve. Temporarily.

Then it comes back.

---

## 1.2 The First Wrong Explanation

At this point, most engineers reach for a familiar explanation:

> “We’re ingesting more data, so IO is higher.”
> 

That sounds reasonable.

But pause for a moment.

You check the numbers.

- Ingestion rate: stable
- Query load: roughly the same
- CPU: not saturated

So if:

- You’re not ingesting significantly more
- You’re not querying significantly more

Then why is IO increasing?

---

## 1.3 A Subtle Observation

You dig deeper.

You notice something interesting.

The system is doing a lot of background work — even when query load is low.

There are processes that:

- Read data
- Write data
- Delete data

But you’re not issuing those operations explicitly.

They’re happening… on their own.

---

## 🤔 Pause Here

Before reading further, try to answer:

> If you insert data once, why would the system need to read and rewrite it again?
> 

Take a moment. This is the key question.

---

## 1.4 The Hidden Mechanism

What you’re seeing is not incidental behavior.

It is the core design of ClickHouse.

When you insert data into a MergeTree table:

- The data is written as a **part**
- That part is immutable
- It is sorted according to ORDER BY
- It is immediately queryable

So far, nothing unusual.

But over time, many such parts accumulate.

And here’s the critical detail:

> ClickHouse does not keep those parts as-is forever.
> 

Instead, it periodically performs **merges**.

---

## 1.5 What a Merge Really Is

A merge is not a metadata operation.

It is not a pointer update.

It is a full data rewrite.

When ClickHouse merges parts:

1. It reads multiple existing parts
2. It decompresses their data
3. It merges them into a single sorted stream
4. It writes a new part
5. It deletes the old parts

Let that sink in.

Every merge is:

- A read of existing data
- A write of new data

---

## 1.6 The First Realization

Go back to your earlier assumption:

> “We write data once.”
> 

That is no longer true.

In reality:

- Data is written once during ingestion
- Then rewritten multiple times during merges

So the system is not just storing data.

It is **continuously reorganizing it**.

---

## 🤔 Pause Again

If a row is:

- Written once during insert
- Then rewritten 3 more times during merges

How many times did that row hit disk?

---

## 1.7 The Amplification Effect

If you follow that through:

- 1 initial write
- 3 rewrite as part of merge

That’s 4 total writes.

Which means:

> Your system may be writing 3–5× more data than you ingest.
> 

And that extra IO?

It doesn’t show up in your ingestion metrics.

But it absolutely shows up in:

- Disk bandwidth
- Object storage requests
- Network utilization

---

## 1.8 Why This Design Exists

At this point, a natural reaction is:

> “Why would a database do this? This seems wasteful.”
> 

But the design is deliberate.

By rewriting data, ClickHouse achieves:

### 1. Better Compression

When small parts are merged:

- Similar values cluster together
- Encoding becomes more effective
- Storage footprint reduces

---

### 2. Better Query Performance

Larger, well-merged parts mean:

- Fewer files to scan
- Better locality
- More effective skipping

---

### 3. Simpler Write Path

Because:

- Inserts are append-only
- No in-place updates
- No locking complexity

---

So the system trades:

- **Write amplification**
for
- **Read efficiency and simplicity**

---

## 1.9 The Mental Model Shift

This leads to a fundamental shift in how you think about the system.

ClickHouse is not:

> “A system that stores data efficiently”
> 

It is:

> “A system that *continuously rewrites data* to maintain efficient structure”
> 

---

## 1.10 The Consequence You Must Internalize

Once you accept this, many things become clearer:

- Why IO grows even if ingestion is stable
- Why small design mistakes explode at scale
- Why merges dominate system behavior
- Why “just adding more data” changes system dynamics

---

## 1.11 The Core Equation

You can now express system IO as:

```
Total IO = Ingestion IO + Merge Rewrite IO
```

And crucially:

> Merge Rewrite IO is often the dominant term.
> 

---

## 1.12 Stress the Model

Let’s test your understanding.

Imagine:

- You completely disable merges (hypothetically)

What happens?

---

Pause and think.

---

### Answer

At first:

- IO drops
- System looks stable

But over time:

- Parts accumulate
- Queries slow down
- Metadata explodes
- Skipping becomes ineffective

Eventually:

> The system collapses from fragmentation instead of IO.
> 

---

## 1.13 The Balanced View

So merges are:

- Necessary for performance
- Expensive in IO

And the entire system becomes a balancing act:

> Enough merges to keep data efficient
> 
> 
> But not so many that IO overwhelms the system
> 

---

## 1.14 Closing Insight

If you take only one thing from this chapter, let it be this:

> ClickHouse does not store data once.
> 
> 
> It rewrites it repeatedly to maintain structure.
> 

Everything you will learn next — parts, partitions, batching, amplification, IO limits — flows from this single truth.