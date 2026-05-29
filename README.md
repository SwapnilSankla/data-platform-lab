## Data Platform Lab
This repository contains a modern tech stack which helps defining Production-Style data pipelines.

### Tech stack
- Apache Airflow (Orchestration)
- Apache Spark (Processing engine)
- MinIO (Object Storage)
- Postgres (Stargate database)

### Dataset
- https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store/2019-Nov.csv

### Run docker compose
- Create `.env` based on `.env.example`  
- Copy `aws-java-sdk-bundle-1.12.262.jar` and `hadoop-aws-3.3.4.jar` into `infrastructure/spark/jars/
- `colima start -c 8 -m 8`
- Run `docker-compose up -d`

### Submit First pipeline to Spark
- `docker exec -it spark-master bash`
- `cd /opt/spark/bin`
- `./spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.ui.port=4040 \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.driver.host=spark-master \
  --conf spark.eventLog.enabled=true \
  --conf spark.eventLog.dir=file:///tmp/spark-events \
  /opt/spark-apps/jobs/first_pipeline.py`

### Notebook setup
- `uv add pyspark==3.5.1` Add Pyspark
- `uv add ipykernel` Install kernel
- `uv run python -m ipykernel install --user --name data-platform-lab` Create Jyputer kernel
- Use Java 17
- Copy `https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store/2019-Nov.csv` to `./datasets/raw`
