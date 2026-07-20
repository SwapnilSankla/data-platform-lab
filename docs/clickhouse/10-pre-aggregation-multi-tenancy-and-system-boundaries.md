## 10.1 The Problem Statement

You are building a platform like Uber.

Data:

- Every ride generates events
- Millions of events per second
- Global scale
- Multiple cities, drivers, riders

Use cases:

- Real-time dashboards (rides per city, hour)
- Driver performance
- Surge pricing analytics
- Rider behavior (limited)
- Internal analytics

---

At first, it seems simple:

> “Let’s dump everything into ClickHouse and query it.”
> 

---

## 🤔 Pause

Based on everything you’ve learned so far…

> What could go wrong?
> 

---

## 10.2 The Naive Architecture

Let’s write it explicitly.

```
Producers → Kafka → ClickHouse (raw table) → Queries
```

Single table:

```
ride_eventsORDERBY (request_time, city_id)
```

---

### Why this feels right

- Simple
- Flexible
- All data in one place

---

### What happens over time

- Data grows to TB → PB
- Queries scan massive data
- Merge IO explodes
- System becomes IO-bound
- Costs increase rapidly

---

## 💡 Insight

> Simplicity at small scale becomes fragility at large scale.
> 

---

## 10.3 The First Evolution — Aggregation

You introduce:

```
Raw Table → Aggregated Table
```

Example:

```
city_hourly_metrics
(
    city_id,
hour,
    ride_count,
    avg_fare
)
```

---

## 🤔 Pause

What changes?

---

### Answer

- Queries now hit smaller tables
- Less data scanned
- Lower IO
- Better latency

---

But raw table still exists.

---

## 10.4 The Second Problem — Multi-Tenancy

Now introduce tenants:

- Different business units
- Or external clients
- Or geographies

Assume:

- 500 tenants
- Top 5 tenants generate 60% of traffic

---

## 🤔 Pause

Should all tenants share the same table?

---

## 10.5 The Naive Answer

> “Yes — just add tenant_id”
> 

```
ORDERBY (request_time, city_id, tenant_id)
```

---

## ❌ Why This Fails

- tenant_id increases cardinality
- Breaks clustering
- Merge efficiency drops
- Large tenants dominate merges
- Small tenants suffer

---

## 💡 Insight

> Logical isolation is not the same as physical isolation.
> 

---

## 10.6 The Correct Strategy — Workload Isolation

Instead of:

> One table for all
> 

You design:

---

### Large Tenants

- Dedicated tables
- Possibly dedicated clusters

---

### Small Tenants

- Shared table

---

## 🤔 Pause

Why isolate only large tenants?

---

### Answer

Because:

> Workload is skewed, not uniform.
> 

---

## 10.7 The Architecture Evolves

Now your system looks like:

```
                ┌───────────────┐
                │ Kafka Stream  │
                └──────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Large Tenant   Large Tenant   Small Tenants
      Pipeline        Pipeline        Pipeline
        │              │              │
        ▼              ▼              ▼
   CH Table A     CH Table B     Shared Table
        │              │              │
        └──────┬───────┴───────┬──────┘
               ▼               ▼
        Aggregated Tables (per segment)
```

---

## 10.8 Where Pre-Aggregation Fits

Pre-aggregation can happen:

---

### Option 1 — Inside ClickHouse

- Materialized views
- Simple but still IO heavy

---

### Option 2 — Upstream (Recommended)

- Spark / Flink jobs
- Write aggregated data directly

---

## 🤔 Pause

Why prefer upstream?

---

### Answer

Because:

> You reduce data before it hits ClickHouse
> 
> 
> → reduces merges
> 
> → reduces IO
> 

---

## 10.9 The Aggregation-First Philosophy

At scale, you shift mindset:

---

### Old

> Raw table is the source of truth for all queries
> 

---

### New

> Aggregated tables are the primary query layer
> 
> 
> Raw table is fallback / audit
> 

---

## 💡 Insight

> Raw data is for completeness
> 
> 
> Aggregated data is for usability
> 

---

## 10.10 Query Routing Layer

Now introduce another layer:

```
User Query → Router → Aggregated / Raw
```

---

### Example

- Dashboard → aggregated table
- Ad-hoc → raw table
- Heavy queries → restricted

---

## 10.11 Protecting the System

You enforce:

- Query limits on raw tables
- Rate limiting
- Sandbox environments

---

## 🤔 Pause

Why restrict raw queries?

---

### Answer

Because:

> Raw queries can bypass all optimizations and break the system.
> 

---

## 10.12 Storage Strategy

Now think in tiers:

---

### Hot Data

- Recent days
- High query frequency
- Stored in ClickHouse

---

### Cold Data

- Historical
- Rarely accessed
- Stored in cheaper storage

---

## 10.13 Merge Pressure Control

With this architecture:

- Raw ingestion reduced (due to aggregation)
- Parts/sec reduced
- Merge amplification reduced

---

## 10.14 Putting It All Together

Let’s trace a full flow.

---

### Step 1 — Event Generation

- Ride events generated

---

### Step 2 — Streaming Layer

- Kafka buffers data

---

### Step 3 — Processing Layer

- Flink/Spark aggregates data
- Produces:
    - Raw stream (optional)
    - Aggregated stream

---

### Step 4 — Storage Layer

- Raw → ClickHouse raw tables
- Aggregated → ClickHouse aggregated tables

---

### Step 5 — Query Layer

- Most queries → aggregated tables
- Rare queries → raw tables

---

### Step 6 — Isolation Layer

- Large tenants separated
- Small tenants pooled

---

## 10.15 What You Achieve

- IO under control
- Merge pressure manageable
- Query latency predictable
- Cost sustainable
- System scalable

---

## 10.16 What You Avoid

- Part explosion
- Merge starvation
- Amplification runaway
- IO collapse
- Cost explosion

---

## 10.17 The Final Mental Model

You are no longer designing:

> A database schema
> 

You are designing:

> A **data processing system with controlled data movement**
> 

---

## 10.18 The Ultimate Insight

If you remember one thing:

> The goal is not to make ClickHouse handle more data.
> 
> 
> The goal is to ensure ClickHouse only sees the data it *should* handle
>