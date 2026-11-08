"""Local PySpark Bronze/Silver/Gold pipeline with deterministic data-quality audit."""
import argparse
from pyspark.sql import SparkSession, Window, functions as F, types as T

COLUMNS = ("order_id", "customer_id", "order_date", "product_id", "quantity", "unit_price")
SCHEMA = T.StructType([T.StructField(c, T.StringType()) for c in COLUMNS])

def classify(bronze):
    """Return accepted and rejected rows; duplicate winner is deterministic.

    Valid duplicates are ordered by normalized business fields, not Spark partition
    order. Identical duplicates are interchangeable. Invalid rows are audited first.
    """
    typed = (bronze
        .withColumn("order_id", F.trim("order_id"))
        .withColumn("customer_id", F.trim("customer_id"))
        .withColumn("product_id", F.trim("product_id"))
        .withColumn("parsed_date", F.expr("try_cast(order_date as date)"))
        .withColumn("parsed_quantity", F.expr("try_cast(quantity as int)"))
        .withColumn("parsed_price", F.expr("try_cast(unit_price as decimal(18,2))")))
    reason = (F.when(F.col("order_id").isNull() | (F.length("order_id") == 0), "missing_order_id")
        .when(F.col("customer_id").isNull() | (F.length("customer_id") == 0), "missing_customer_id")
        .when(F.col("product_id").isNull() | (F.length("product_id") == 0), "missing_product_id")
        .when(F.col("parsed_date").isNull(), "invalid_order_date")
        .when(F.col("parsed_quantity").isNull() | (F.col("parsed_quantity") <= 0), "invalid_quantity")
        .when(F.col("parsed_price").isNull() | (F.col("parsed_price") < 0), "invalid_unit_price"))
    assessed = typed.withColumn("rejection_reason", reason)
    invalid = assessed.filter(F.col("rejection_reason").isNotNull())
    valid = assessed.filter(F.col("rejection_reason").isNull())
    ordering = [F.col(c).asc_nulls_last() for c in
                ("customer_id", "product_id", "parsed_date", "parsed_quantity", "parsed_price")]
    ranked = valid.withColumn("_rank", F.row_number().over(
        Window.partitionBy("order_id").orderBy(*ordering)))
    duplicate = (ranked.filter(F.col("_rank") > 1)
                 .drop("_rank").withColumn("rejection_reason", F.lit("duplicate_order_id")))
    accepted = (ranked.filter(F.col("_rank") == 1)
        .select("order_id", "customer_id", "product_id",
                F.col("parsed_date").alias("order_date"),
                F.col("parsed_quantity").alias("quantity"),
                F.col("parsed_price").alias("unit_price")))
    rejected = (invalid.unionByName(duplicate)
        .select(*COLUMNS, "rejection_reason"))
    return accepted, rejected

def transform(spark, source, destination):
    """Write Bronze, Silver, rejected audit, and Gold Parquet; return counts."""
    bronze = spark.read.option("header", True).schema(SCHEMA).csv(str(source))
    bronze.write.mode("overwrite").parquet(f"{destination}/bronze/orders")
    silver, rejected = classify(bronze)
    silver.write.mode("overwrite").parquet(f"{destination}/silver/orders")
    rejected.write.mode("overwrite").parquet(f"{destination}/silver/rejected_orders")
    gold = (silver.withColumn("line_revenue", F.col("quantity") * F.col("unit_price"))
        .groupBy("order_date", "product_id")
        .agg(F.count("*").alias("order_count"),
             F.sum("quantity").alias("units_sold"),
             F.sum("line_revenue").cast("decimal(20,2)").alias("revenue")))
    gold.write.mode("overwrite").parquet(f"{destination}/gold/daily_product_sales")
    return {"bronze": bronze.count(), "silver": silver.count(),
            "rejected": rejected.count(), "gold": gold.count()}

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
