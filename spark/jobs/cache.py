
from pyspark.sql import SparkSession
import os

minio_access_key = os.getenv("MINIO_ACCESS_KEY")
minio_secret_key = os.getenv("MINIO_SECRET_KEY")

spark = SparkSession \
    .builder \
    .appName("cache") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", minio_access_key) \
    .config("spark.hadoop.fs.s3a.secret.key", minio_secret_key) \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .getOrCreate()

df = spark \
    .read \
    .option("header", "true") \
    .option("inferSchema", "false") \
    .csv("s3a://clickstream/2019-Nov.csv")

purchase_events = df.filter("event_type='purchase'")
purchase_events.cache()

purchase_events_count = purchase_events.count()
print(f"Row Count: {purchase_events_count}")

purchase_events_group_by_brand_counts = purchase_events.groupBy("brand").count()
purchase_events_group_by_brand_counts.show()

spark.stop()