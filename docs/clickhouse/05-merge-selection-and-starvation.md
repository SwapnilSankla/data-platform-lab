## 5.1 A System That Refuses to “Fix Itself”

Let’s revisit a familiar situation.

You have:

- Continuous ingestion
- Reasonable batching (not terrible)
- Time-based partitioning
- Enough hardware

Yet, over time, you observe:

- Many small parts still exist
- Large parts are forming… but slowly
- Merge backlog is growing

You look at the system and think:

> “Why doesn’t ClickHouse just merge all these small parts quickly and be done with it?”
> 

---

## 🤔 Pause

If you had complete control, what would you do?

- Merge everything aggressively?
- Always prioritize largest merges?
- Always clean up smallest parts first?

Hold that thought.

---

## 5.2 The Naive Strategy (And Why It Fails)

Let’s say you design a “perfect” merge strategy:

> “Always merge as many parts as possible into one big part.”
> 

Sounds ideal.

---

### What happens?

- Huge merges start
- Each merge reads massive data
- IO spikes
- Queries slow down
- System becomes unstable

So this strategy is not viable.

---

## 5.3 The Opposite Strategy

Now try the opposite:

> “Only merge very small parts.”
> 

---

### What happens?

- Small parts get merged into medium parts
- But medium parts never get merged further
- System accumulates mid-sized parts
- Amplification still high

Again — not ideal.

---

## 5.4 The Reality: Heuristic Scheduling

ClickHouse does not use a globally optimal merge plan.

Instead, it uses **heuristics**.

At a high level:

- Prefer merging parts of similar size
- Avoid very large merges unless necessary
- Keep merges incremental
- Balance IO usage

This is practical — but not perfect.

---

## 5.5 The Merge Ladder (Revisited with Behavior)

Recall the levels:

```
L0 → L1 → L2 → L3 → L4
```

Now add behavior:

- System prefers merging within same level
- Progression to next level is gradual
- Larger merges are rarer

---

## 🤔 Pause

If new small parts keep arriving continuously…

What happens to this ladder?

---

## 5.6 The Core Problem: Continuous Pressure

Let’s walk through it slowly.

### Step 1

New small parts arrive → L0 fills up

### Step 2

Merge scheduler picks small parts → L1 formed

### Step 3

But before L1 can be merged further…

More L0 parts arrive

---

## 🤯 The Consequence

The system keeps doing:

```
L0 → L1 → L0 → L1 → L0 → L1
```

But struggles to do:

```
L1 → L2 → L3
```

---

## 💡 Insight

> The system gets stuck in lower levels.
> 

This is **merge starvation**.

---

## 5.7 What Is Starvation?

Merge starvation means:

> Higher-level merges are delayed indefinitely because lower-level work never stops.
> 

---

## 🤔 Think

Which merges are cheaper?

- Small merges (L0 → L1)
- Large merges (L2 → L3)

---

### Answer

Small merges.

---

## 5.8 The Scheduler’s Bias

Because small merges:

- Require less IO
- Finish faster
- Are safer

The scheduler tends to:

> Keep picking small merges
> 

---

## 🤯 The Paradox

This leads to a paradox:

> The system keeps doing the “easy work”
> 
> 
> and postpones the “important work”
> 

---

## 5.9 The Resulting State

You end up with:

- Many small and medium parts
- Few large consolidated parts
- High amplification
- Persistent merge backlog

---

## 5.10 Why This Is Hard to See

From outside, the system looks active:

- Merges are happening
- CPU is doing work
- IO is flowing

So it feels like:

> “System is working hard”
> 

But in reality:

> It’s working on the wrong level of the problem.
> 

---

## 5.11 A More Intuitive Analogy

Think of it like cleaning a warehouse.

- New boxes arrive constantly
- Workers keep organizing small boxes
- But never get time to consolidate large sections

So the warehouse is:

- Busy
- Active
- Still messy

---

## 5.12 The Feedback Loop

Let’s connect the dots.

1. Small parts arrive continuously
2. Scheduler prefers small merges
3. Large merges delayed
4. Amplification increases
5. IO increases
6. Merge speed decreases
7. Backlog grows
8. Even more pressure on small merges

---

This is a **self-reinforcing loop**.

---

## 5.13 The Hidden Trigger

Notice something important:

> Starvation is not caused by lack of resources.
> 

It is caused by:

> The combination of continuous ingestion + merge heuristics
> 

---

## 5.14 The Wrong Fix

At this point, many engineers try:

- Increase merge threads
- Increase CPU
- Increase memory

---

## 🤔 Pause

Will this fix starvation?

---

### Answer

Not necessarily.

Because:

- More threads still follow same heuristic
- IO remains the bottleneck
- You may increase contention

---

## 5.15 The Correct Fix

To break starvation, you must:

> Reduce pressure on lower levels
> 

---

### How?

1. Increase batch size
    - Fewer small parts
    - Less L0 pressure
2. Reduce parts/sec
    - Give system time to climb levels
3. Improve merge efficiency
    - Larger initial parts

---

## 💡 Insight

> You don’t fix starvation by speeding up merges.
> 
> 
> You fix it by reducing the amount of small work entering the system.
> 

---

## 5.16 A Subtle Observation

You might see:

- Merges are happening
- But part sizes not increasing significantly

That is a red flag.

---

## 🤔 Pause

If merges are happening but part sizes don’t grow…

What does that mean?

---

### Answer

System is stuck in lower levels → starvation.

---

## 5.17 Connecting All Chapters

Now connect everything:

- Chapter 2: parts/sec matters
- Chapter 3: small parts increase levels
- Chapter 4: more levels → amplification
- Chapter 5: scheduler can get stuck in lower levels

---

## 5.18 Final Mental Model

The system is like:

```
Incoming parts → merge pipeline → final large parts
```

If input pressure is too high:

> Pipeline never completes.
> 

---

## 5.19 Closing Insight

If you remember one thing:

> ClickHouse merge system is not globally optimal —
> 
> 
> it is locally efficient and can get stuck under continuous pressure.
> 

---

# 🔚 End of Chapter 5

---

Next:

👉 **Chapter 6 — ORDER BY as a Physical Design Tool**

We’ll shift gears slightly:

- From *writes and merges*
- To *how data is physically laid out for reads*

This is where your earlier ClickHouse intuition (city, time, rider) will connect deeply.

---

Before we proceed:

Do you want Chapter 6 to include:

- Your earlier ride_events examples (city, driver, rider)
👉 This will make it very concrete

Or keep it generic?