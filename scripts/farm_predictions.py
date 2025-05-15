import os
import uuid
from datetime import datetime

import numpy as np
from joblib import load
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, DoubleType, IntegerType, BooleanType
)
from pyspark.sql.functions import (
    col, from_json, avg, sum as _sum, first, lit, count
)
from inference_kaggle import inference
from load_kaggle_model import load_prediction_model

from config_loader import get_postgres_uri
get_postgres_uri = get_postgres_uri()
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT", 5432)
db = os.getenv("POSTGRES_DB")
# ----------------------------------------------------------------------------
# 1. Stream-instance UUID
# ----------------------------------------------------------------------------

STREAM_ID = os.getenv("STREAM_ID", uuid.uuid4().hex[:8])
print(f"[info] Stream instance ID = {STREAM_ID}")

# ----------------------------------------------------------------------------
# 2. Spark session
# ----------------------------------------------------------------------------

spark = (
    SparkSession.builder
    .appName("FarmMetricsAggregator")
    .config("spark.jars.packages", os.getenv("JDBC_JAR", "org.postgresql:postgresql:42.7.3"))
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ----------------------------------------------------------------------------
# 3. Kafka source
# ----------------------------------------------------------------------------

kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    .option("subscribe", os.getenv("TOPIC", "farm_predictions"))
    .option("startingOffsets", "latest")
    .load()
)

schema = StructType([
    StructField("rainfall", DoubleType(), True),
    StructField("soil_quality_index", IntegerType(), True),
    StructField("farm_size_hectares", DoubleType(), True),
    StructField("sunlight_hours", DoubleType(), True),
    StructField("fertilizer", IntegerType(), True),
])

parsed_df = (
    kafka_df.selectExpr("CAST(value AS STRING) AS json_str")
    .select(from_json(col("json_str"), schema).alias("data"))
    .select("data.*")
)

# ----------------------------------------------------------------------------
# 4. Load prediction model
# ----------------------------------------------------------------------------

MODEL_PATH = os.getenv("MODEL_PATH", "yield_model.joblib")
try:
    model = load_prediction_model()
    # model = load(MODEL_PATH)
    print(f"[info] Model loaded from {MODEL_PATH}")
except Exception as exc:
    model = None
    print(f"[warn] Could not load model: {exc}. Using 0.0 fallback.")

# ----------------------------------------------------------------------------
# 5. Batch processing
# ----------------------------------------------------------------------------

def process_batch(batch_df, batch_id):
    if batch_df.rdd.isEmpty():
        print(f"Batch {batch_id}: empty-skipped")
        return

    base_df = (
        batch_df.agg(
            count("*").alias("records_count"),
            avg("rainfall").alias("avg_rainfall"),
            avg("sunlight_hours").alias("avg_sunlight_hours"),
            _sum("fertilizer").alias("total_fertilizer"),
            first("soil_quality_index").alias("soil_quality_index"),
            first("farm_size_hectares").alias("farm_size_hectares"),
        )
        .withColumn("batch_id", lit(batch_id))
        .withColumn("stream_id", lit(STREAM_ID))
        .withColumn("processed_at", lit(datetime.utcnow()))
    )

    # ---------- prediction ----------
    metrics = base_df.collect()[0].asDict()
    vec = np.array([
        metrics["avg_rainfall"],
        metrics["avg_sunlight_hours"],
        metrics["total_fertilizer"],
        metrics["soil_quality_index"],
        metrics["farm_size_hectares"],
    ]).reshape(1, -1)

    pred = 0.0
    is_proc = False
    try:
        if model:
            # pred = float(model.predict(vec)[0])
            pred = float(inference(model, vec)[0])
            is_proc = True
    except Exception as exc:
        print(f"[error] Model failed on batch {batch_id}: {exc} - fallback 0.0")

    enriched_df = (
        base_df
        .withColumn("predicted_yield", lit(pred).cast(DoubleType()))
        .withColumn("is_processed", lit(is_proc).cast(BooleanType()))
    )

    jdbc_url = os.getenv("JDBC_URL", f"jdbc:postgresql://{host}:{port}/{db}")
    props = {
        "user": user,
        "password": password,
        "driver": "org.postgresql.Driver",
    }

    enriched_df.write.mode("append").jdbc(jdbc_url, "farm_metrics", properties=props)

    print(
        f"Batch {batch_id} (stream {STREAM_ID}) → records {metrics['records_count']} | pred {pred} | processed {is_proc}"
    )

# ----------------------------------------------------------------------------
# 6. Start query
# ----------------------------------------------------------------------------

(
    parsed_df.writeStream
    .outputMode("append")
    .foreachBatch(process_batch)
    .start()
    .awaitTermination()
)
