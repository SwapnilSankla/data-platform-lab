
from pyspark.sql import SparkSession
import os

minio_access_key = os.getenv("MINIO_ACCESS_KEY")
minio_secret_key = os.getenv("MINIO_SECRET_KEY")

spark = SparkSession \
    .builder \
    .appName("wide-transformation") \
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

event_counts = df.groupBy("event_type").count()

event_counts.show()

spark.stop()