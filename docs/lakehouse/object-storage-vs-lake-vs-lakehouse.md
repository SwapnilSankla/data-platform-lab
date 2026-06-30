## Object Storage vs Data Lake vs Lakehouse

### Object Storage
- Provides scalable object/blob storage
- Highly durable and cost effective
- Decouples storage from compute
- Exposes object-based APIs
- Examples: S3, MinIO, GCS

---

### Data Lake
- Architectural pattern built on top of object storage
- Organizes analytical datasets for scalable processing

Data lake architecture defines:
1. Raw vs processed zones
2. Partitioning strategies
3. File organization
4. Historical immutable storage

Typical setup:
1. Object storage
2. File formats like Parquet/Avro
3. Analytical engines like Spark/Trino
4. Partitioning schemes (commonly time-based)

---

### Lakehouse
- Extends data lake architecture with warehouse-like table semantics
- Adds metadata and transactional layers on top of object storage

Open table formats:
- Iceberg
- Delta Lake
- Hudi

Enables:
1. ACID transactions
2. Time travel
3. Schema evolution
4. Better metadata management
5. Partition pruning and query optimization