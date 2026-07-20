## 3.1 A System That Looks “Almost Fine”

Let’s construct a scenario.

You’ve already learned your lesson from Chapter 2.

So you are **not** inserting one row at a time.

Instead:

- Batch size: ~50,000 rows
- Ingestion: steady
- Partitioning: time-based (reasonable)

On paper, this should be fine.

And initially — it is.

---

After a few days:

- System is stable
- Queries are fast
- Merges are happening

But as data grows:

- Merge backlog slowly increases
- IO usage keeps creeping up
- Some queries degrade

Nothing catastrophic. Just… uncomfortable.

---

## 🤔 Pause

You’re already batching.

So ask yourself:

> Why is the system still struggling?
> 

---

## 3.2 The First Wrong Explanation

A common reaction:

> “Maybe we need more hardware.”
> 

That might help temporarily.

But you already know from Chapter 1:

> IO problems often come from amplification, not raw volume.
> 

So adding hardware may just delay the problem.

---

## 3.3 Looking Deeper: What Is a “Small Part”?

We need to define this carefully.

A “small part” is not about rows alone.

It is about:

- Total size (MB/GB)
- Number of granules
- How much work it represents in merges

For example:

- 50k rows might be:
    - ~5–20 MB (depending on schema)

That is **tiny** in analytical systems.

---

## 3.4 Why Size Matters More Than You Think

Let’s imagine your system is continuously creating these small parts.

Every second:

- New 50k-row parts arrive
- Merge system starts working

Now, think about how parts evolve.

---

## 🤔 Pause

If you start with many small parts, how do you get to large parts?

---

## 3.5 The Merge Ladder

Parts don’t jump from small → huge instantly.

They grow gradually:

```
Level 0: 50k rows
Level 1: 200k rows
Level 2: 800k rows
Level 3: 3M rows
Level 4: 12M rows
...
```

Each level requires a **merge**.

Each merge requires:

- Reading input parts
- Writing output part

---

## 3.6 The Hidden Cost: Depth

Now we arrive at the real issue.

Small parts don’t just increase count.

They increase **merge depth**.

---

## 🤔 Think Carefully

If you start with:

- Very small parts → many levels needed
- Larger parts → fewer levels needed

Which system rewrites data more times?

---

### Answer

The one with smaller parts.

---

## 3.7 From Count to Amplification

Let’s connect this with Chapter 1.

If each level rewrites data:

- Small parts → more levels → more rewrites
- Large parts → fewer levels → fewer rewrites

So:

```
smaller parts → higher amplification
```

---

## 3.8 A Concrete Example

Let’s make this tangible.

### Case A — Small Parts

Start with 50k rows per part:

- Need ~5 merge levels to reach large part
- Each row rewritten ~5 times

---

### Case B — Larger Parts

Start with 500k rows per part:

- Need ~2 merge levels
- Each row rewritten ~2 times

---

## 🤔 Pause

Same data.

Which system generates more IO?

---

### Answer

Case A — significantly more.

---

## 3.9 The Compounding Effect

Here’s the subtlety:

This is not linear.

It compounds.

Because:

- More parts → more merges
- More merges → more IO
- More IO → slower merges
- Slower merges → backlog grows
- Backlog → even more parts

This is a **feedback loop**.

---

## 3.10 The System Spiral

Let’s describe the failure mode:

1. Small parts created frequently
2. Merge system tries to catch up
3. IO increases
4. Merge speed drops (IO contention)
5. Parts accumulate
6. Even more merges required
7. System enters unstable state

---

## 💡 Key Insight

> Small parts don’t just increase work.
> 
> 
> They create a **self-reinforcing instability loop**.
> 

---

## 3.11 Why This Is Worse in Object Storage

(We’ll go deeper later, but a preview)

Each part:

- Is a set of files / objects
- Requires network IO
- Has latency overhead

So:

- More parts → more requests
- More requests → more latency
- More latency → slower merges

Small parts amplify this effect.

---

## 3.12 The Misleading Stability Phase

This is important.

Small parts don’t break the system immediately.

They:

- Work fine at small scale
- Gradually degrade
- Fail only after accumulation

This is why teams often:

> “Don’t see the problem coming”
> 

---

## 3.13 The Real Definition of “Healthy”

A healthy system is not:

- Low CPU
- Fast queries

A healthy system is:

> Parts are growing steadily into larger sizes
> 

---

## 🤔 Pause

If you observe:

- Many small parts
- Few large parts

What does that indicate?

---

### Answer

Merge pipeline is not progressing.

System is at risk.

---

## 3.14 The Correct Lever (Revisited)

At this point, the solution becomes clearer.

To fix small-part problems:

- Increase batch size
- Reduce parts/sec
- Ensure parts start larger

Not:

- Change ORDER BY
- Add indexes
- Tune queries

---

## 3.15 Stress Test

Suppose:

- You double batch size
- Parts become 2× larger

What happens?

---

Pause.

---

### Answer

- Merge levels reduce
- Rewrite count reduces
- IO reduces
- System stabilizes

---

## 3.16 The Deep Connection

Now connect Chapters 1–3:

- Chapter 1: Data is rewritten
- Chapter 2: Parts control merge workload
- Chapter 3: Part size controls rewrite depth

---

## 3.17 Final Mental Model

You can now think of the system as:

```
Insert → Parts → Merge Levels → IO → Stability
```

And the most powerful lever is:

> Part size at creation
> 

---

## 3.18 Closing Insight

If you remember one thing:

> Small parts are dangerous not because they are many,
> 
> 
> but because they force the system to rewrite data *many more times*.
>