"""Daily Airflow DAG: transactional ingestion -> quality gate -> SQL report.

Workers must share access to the configured source and SQLite database.
"""
import os
from datetime import datetime, timedelta, timezone
from airflow import DAG
from airflow.operators.python import PythonOperator
from retail_pipeline.orchestration import ingest, quality_gate, publish_report

SOURCE = os.environ.get("RETAIL_SOURCE", "/opt/airflow/data/sample_orders.csv")
DATABASE = os.environ.get("RETAIL_DB", "/opt/airflow/outputs/checkpoints.sqlite")
REPORT = os.environ.get("RETAIL_REPORT", "/opt/airflow/outputs/warehouse_report.json")
MAX_REJECTION_RATIO = float(os.environ.get("RETAIL_MAX_REJECTION_RATIO", "0.25"))

with DAG(
    dag_id="retail_daily_warehouse",
    description="Replay-safe retail ingestion with data quality and reporting",
    start_date=datetime(2026, 11, 1, tzinfo=timezone.utc),
    schedule="0 6 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "data-platform", "retries": 2,
                  "retry_delay": timedelta(minutes=5)},
    tags=["retail", "data-quality", "warehouse"],
) as dag:
    ingest_orders = PythonOperator(task_id="ingest_orders", python_callable=ingest,
                                   op_kwargs={"source": SOURCE, "database": DATABASE})
    check_quality = PythonOperator(task_id="check_quality", python_callable=quality_gate,
                                   op_kwargs={"database": DATABASE, "max_rejection_ratio": MAX_REJECTION_RATIO})
    publish_warehouse = PythonOperator(task_id="publish_warehouse", python_callable=publish_report,
                                       op_kwargs={"database": DATABASE, "destination": REPORT})
    ingest_orders >> check_quality >> publish_warehouse
