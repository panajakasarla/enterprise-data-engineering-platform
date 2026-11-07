"""Local PySpark Bronze/Silver/Gold retail orders pipeline."""
import argparse
from pyspark.sql import SparkSession, functions as F, types as T

SCHEMA = T.StructType([T.StructField(c, T.StringType()) for c in
    ("order_id", "customer_id", "order_date", "product_id", "quantity", "unit_price")])

def transform(spark, source, destination):
    """Write raw, validated, and aggregated Parquet layers; return row counts."""
    bronze = spark.read.option("header", True).schema(SCHEMA).csv(str(source))
    bronze.write.mode("overwrite").parquet(f"{destination}/bronze/orders")
    typed = (bronze
        .withColumn("order_id", F.trim("order_id"))
        .withColumn("customer_id", F.trim("customer_id"))
        .withColumn("product_id", F.trim("product_id"))
        .withColumn("parsed_date", F.to_date("order_date", "yyyy-MM-dd"))
        .withColumn("parsed_quantity", F.expr("try_cast(quantity as int)"))
        .withColumn("parsed_price", F.expr("try_cast(unit_price as decimal(18,2))")))
    silver = (typed
        .filter(F.col("order_id").isNotNull() & (F.length("order_id") > 0))
        .filter(F.col("customer_id").isNotNull() & (F.length("customer_id") > 0))
        .filter(F.col("product_id").isNotNull() & (F.length("product_id") > 0))
        .filter(F.col("parsed_date").isNotNull())
        .filter(F.col("parsed_quantity") > 0)
        .filter(F.col("parsed_price") >= 0)
        .dropDuplicates(["order_id"])
        .select("order_id", "customer_id", "product_id",
                F.col("parsed_date").alias("order_date"),
                F.col("parsed_quantity").alias("quantity"),
                F.col("parsed_price").alias("unit_price")))
    silver.write.mode("overwrite").parquet(f"{destination}/silver/orders")
    gold = (silver.withColumn("line_revenue", F.col("quantity") * F.col("unit_price"))
        .groupBy("order_date", "product_id")
        .agg(F.count("*").alias("order_count"),
             F.sum("quantity").alias("units_sold"),
             F.sum("line_revenue").cast("decimal(20,2)").alias("revenue")))
    gold.write.mode("overwrite").parquet(f"{destination}/gold/daily_product_sales")
    return {"bronze": bronze.count(), "silver": silver.count(), "gold": gold.count()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    spark = SparkSession.builder.master("local[*]").appName("RetailMedallion").getOrCreate()
    try:
        print(transform(spark, args.source, args.destination))
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
