"""
Spark job to generate user features from events and write to the data lake for Feast.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, when, max as spark_max

def main():
    spark = SparkSession.builder \
        .appName("GenerateUserFeatures") \
        .getOrCreate()

    # Read events from the data lake (assuming JSON files in partitioned directories)
    events_df = spark.read.json("./data_lake/*/*")

    # Compute user features
    user_features_df = events_df.groupBy("user_id").agg(
        spark_max("timestamp").alias("timestamp"),
        sum(when(col("event_type") == "view", 1).otherwise(0)).alias("total_views"),
        sum(when(col("event_type") == "click", 1).otherwise(0)).alias("total_clicks"),
        sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("total_purchases"),
        sum(when(col("event_type") == "purchase", col("price")).otherwise(0)).alias("total_spent")
    )

    # Write user features to Parquet in the data lake for Feast to read
    user_features_df.write.mode("overwrite").parquet("./data_lake/user_features/")

    spark.stop()

if __name__ == "__main__":
    main()