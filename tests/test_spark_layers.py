"""Spark integration tests for deterministic deduplication and rejection audit."""
import tempfile
import unittest
from pathlib import Path
try:
    from pyspark.sql import SparkSession
    from retail_pipeline.spark_layers import transform
except ImportError:
    SparkSession = None

@unittest.skipIf(SparkSession is None, "pyspark not installed")
class SparkLayersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder.master("local[2]").appName("retail-test").getOrCreate()

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_medallion_counts_reasons_and_revenue(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "orders.csv"
            source.write_text("order_id,customer_id,order_date,product_id,quantity,unit_price\n"
                              "A,C9,2026-11-01,P1,2,10.00\n"
                              "A,C1,2026-11-01,P1,2,10.00\n"
                              "B,C2,2026-11-01,P1,3,5.00\n"
                              "C,C3,2026-11-01,P2,-1,10.00\n"
                              "D,C4,not-a-date,P2,1,5.00\n")
            target = Path(tmp) / "lake"
            expected = {"bronze": 5, "silver": 2, "rejected": 3, "gold": 1}
            self.assertEqual(transform(self.spark, source, target), expected)
            silver = self.spark.read.parquet(str(target / "silver/orders"))
            self.assertEqual(silver.filter("order_id = 'A'").first()["customer_id"], "C1")
            rejected = self.spark.read.parquet(str(target / "silver/rejected_orders"))
            reasons = {r["rejection_reason"] for r in rejected.collect()}
            self.assertEqual(reasons, {"duplicate_order_id", "invalid_quantity", "invalid_order_date"})
            gold = self.spark.read.parquet(str(target / "gold/daily_product_sales")).first()
            self.assertEqual(str(gold["revenue"]), "35.00")
            self.assertEqual(gold["units_sold"], 5)
            self.assertEqual(transform(self.spark, source, target), expected)

if __name__ == "__main__":
    unittest.main()
