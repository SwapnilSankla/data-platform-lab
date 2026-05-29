from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
import os

minio_access_key = os.getenv("MINIO_ACCESS_KEY")
minio_secret_key = os.getenv("MINIO_SECRET_KEY")

spark = SparkSession \
    .builder \
    .appName("generate-user-dimension-dataset") \
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

user_dimension = df \
    .select("user_id") \
    .distinct() \
    .withColumn("user_id_int", col("user_id").cast("long")) \
    .withColumn("country", 
                when((col("user_id_int") % 5) == 1, "IN")
                .when((col("user_id_int") % 5) == 2, "US")
                .when((col("user_id_int") % 5) == 3, "UK")
                .when((col("user_id_int") % 5) == 4, "CA")
                .otherwise("BR")) \
    .drop("user_id_int")

user_dimension.write.parquet("s3a://users/users.parquet")

spark.stop()