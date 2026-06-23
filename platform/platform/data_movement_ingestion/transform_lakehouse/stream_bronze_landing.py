"""
Databricks Structured Streaming job for Kafka -> Bronze Delta.

Design fix:
- Includes SASL JAAS config.
- Uses startingOffsets explicitly.
- Keeps raw records and adds ingest metadata.
- Does not apply business-quality filtering in Bronze.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, from_json, sha2, concat_ws
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

spark = SparkSession.builder.appName("VoltSentinel_Bronze_SCADA").getOrCreate()

telemetry_schema = StructType([
    StructField("timestamp_utc", StringType(), True),
    StructField("asset_id", StringType(), True),
    StructField("measured_generation_kw", DoubleType(), True),
    StructField("expected_available_kw", DoubleType(), True),
    StructField("grid_limit_kw", DoubleType(), True),
    StructField("operating_status", StringType(), True),
    StructField("telemetry_quality", StringType(), True),
    StructField("source_system", StringType(), True),
])

kafka_bootstrap = dbutils.secrets.get("sentinel_vault", "upstash-kafka-bootstrap")
kafka_username = dbutils.secrets.get("sentinel_vault", "upstash-kafka-username")
kafka_password = dbutils.secrets.get("sentinel_vault", "upstash-kafka-password")
jaas_config = (
    'org.apache.kafka.common.security.scram.ScramLoginModule required '
    f'username="{kafka_username}" password="{kafka_password}";'
)

raw_kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", kafka_bootstrap)
    .option("subscribe", "clearway-scada-realtime")
    .option("startingOffsets", "earliest")
    .option("kafka.security.protocol", "SASL_SSL")
    .option("kafka.sasl.mechanism", "SCRAM-SHA-256")
    .option("kafka.sasl.jaas.config", jaas_config)
    .load()
)

bronze_df = (
    raw_kafka_df
    .select(
        col("key").cast("string").alias("kafka_key"),
        col("topic").alias("kafka_topic"),
        col("partition").alias("kafka_partition"),
        col("offset").alias("kafka_offset"),
        col("timestamp").alias("kafka_timestamp"),
        col("value").cast("string").alias("raw_payload"),
        from_json(col("value").cast("string"), telemetry_schema).alias("data"),
    )
    .select("kafka_key", "kafka_topic", "kafka_partition", "kafka_offset", "kafka_timestamp", "raw_payload", "data.*")
    .withColumn("bronze_ingested_at", current_timestamp())
    .withColumn("event_id", sha2(concat_ws("|", col("asset_id"), col("timestamp_utc"), col("kafka_partition"), col("kafka_offset")), 256))
)

query = (
    bronze_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "abfss://bronze@stvoltsentinelprod.dfs.core.windows.net/checkpoints/scada_telemetry")
    .partitionBy("asset_id")
    .trigger(availableNow=True)
    .start("abfss://bronze@stvoltsentinelprod.dfs.core.windows.net/tables/clearway_telemetry")
)

query.awaitTermination()
