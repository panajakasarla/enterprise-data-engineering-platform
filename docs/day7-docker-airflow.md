# Day 7 — Containerized Airflow demonstration

## Goal
Run the existing retail DAG in a reproducible, pinned Apache Airflow image without
installing Airflow into the Python unit-test environment.

## Quick start
Requires Docker Engine / Docker Desktop with Compose v2.

```bash
docker compose build airflow
docker compose up -d airflow
docker compose logs -f airflow
```

Airflow's standalone mode initializes a local metadata database and starts the
scheduler and webserver. Open http://localhost:8080. Retrieve the generated
admin credentials from container logs (do not commit credentials).

The DAG `retail_daily_warehouse` is scheduled at 06:00 UTC. To trigger a run
manually after the container is ready:

```bash
docker compose exec airflow airflow dags trigger retail_daily_warehouse
```

To validate DAG parsing without starting the long-running services:

```bash
bash scripts/check_airflow_dag.sh
```

The script builds the image, lists import errors and confirms the DAG appears in
Airflow's DAG registry. Run `python -m unittest discover -s tests -v` for
the faster no-Docker regression suite.

## Persistence and configuration
The fixture directory is mounted read-only. Named volumes retain Airflow state
and SQLite checkpoints/reports across container restarts. The demo sets
`RETAIL_MAX_REJECTION_RATIO=0.50` because the fixture has 2 rejected rows out
of 5. The production-oriented default in the Python module remains 0.25.

To stop, run `docker compose down`. **Do not use `down -v` unless you
intend to delete the Airflow metadata, checkpoints and report data.**

## Security and operational limits
This is a single-container local learning environment, not production
deployment. Web UI is bound to 127.0.0.1 only. Standalone mode uses
SequentialExecutor and a local SQLite metadata database. The retail pipeline
also uses SQLite; do not scale to multiple writers/workers. Airflow's generated
credentials are for local use only. Container image pinning is by tag, not
immutable digest; production deployments should pin digests, use a supported
external metadata database, secret management and an appropriate executor.

## Verification
The fast configuration tests are static checks. The container DAG smoke test
requires a working Docker daemon and image build; successful GitHub commits do
not prove it passed. The CI workflow includes an optional Docker smoke job to
exercise DAG imports on GitHub-hosted runners.

## Next
Add structured metrics, per-batch quality gates, and cloud deployment IaC.
