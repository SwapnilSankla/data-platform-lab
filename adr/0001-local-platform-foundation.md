# ADR-0001: Local Data Platform Foundation

## Context
Need a local environment to learn production-style
data platform engineering.

## Decision
Use:
- MinIO
- Spark
- Airflow
- PostgreSQL
- Docker Compose

## Why

### MinIO
- MinIO offers S3 compatible APIs for local development
- If someone chooses AWS cloud then S3 becomes the de-facto choice for storage. It is cost effective.
- S3 is very much suitable for very high workload and offers decent archive features and tiering like Standard IA, Glacier.
- Using S3, we can apply patterns like Medallion architecture to create a functional and reproducible data pipelines

### Spark
- We can manage with something like pandas when the workload can fit into a single machine. However, for the higher workloads we need a battle tested distributed engine which offers fast processing.
- With it's unique architecture to support distributed processing, supporting both JVM based and Python based workloads makes it versatile choice.

### Airflow
- Modern day pipelines needs more than just a cron or manual invocation.
- There could be several sources which may need to consumed, sensed to start processing. Modern workloads can't be fit into a single pipeline. Rather, we need to create DAG like structure to facilitate processing. Airflow makes it very easy to support such structures.
- Provides several connectors which makes it easy to connect with wide variety of data tools. 


### PostgreSQL
- offers simplest store upon which the APIs can be built to serve the data pipeline outcomes.
- It offers ACID, transactional support however it is less likely to be useful in the context of the data world. It's the simplicity which makes Postgres as a decent choice to start with.


## Tradeoffs
- Preferring local over cloud for faster learning.
- Not going for tools like Dagster, Prefect for Orchestration or Ray for processing, as the focus is to learn the foundation than tooling.