"""Integration test for PySpark lakehouse; skips if PySpark unavailable."""
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

    def test_medallion_counts_and_revenue(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "orders.csv"
            source.write_text("order_id,customer_id,order_date,product_id,quantity,unit_price\n"
                              "A,C1,2026-11-01,P1,2,10.00\n"
                              "B,C2,2026-11-01,P1,3,5.00\n"
                              "C,C3,2026-11-01,P2,-1,10.00\n"
                              "A,C4,2026-11-01,P1,2,10.00\n")
            target = Path(tmp) / "lake"
            self.assertEqual(transform(self.spark, source, target),
                             {"bronze": 4, "silver": 2, "gold": 1})
            gold = self.spark.read.parquet(str(target / "gold/daily_product_sales")).collect()
            self.assertEqual(str(gold[0]["revenue"]), "35.00")
            self.assertEqual(gold[0]["units_sold"], 5)

if __name__ == "__main__":
    unittest.main()
