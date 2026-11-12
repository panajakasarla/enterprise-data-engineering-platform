#!/usr/bin/env bash
set -euo pipefail

# Run against the same container image used for the local demonstration.
docker compose build airflow
docker compose run --rm --no-deps airflow airflow dags list-import-errors
docker compose run --rm --no-deps airflow airflow dags list | grep -F 'retail_daily_warehouse'
echo 'Airflow DAG import smoke check completed'
