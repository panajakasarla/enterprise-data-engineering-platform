# Local portfolio demonstration; pin the Airflow/Python base image.
FROM apache/airflow:2.10.5-python3.11

USER airflow
WORKDIR /opt/airflow
COPY --chown=airflow:root pyproject.toml README.md ./
COPY --chown=airflow:root src/ ./src/
# The base image supplies Airflow; install only the local pipeline package.
RUN pip install --no-cache-dir --no-deps .
COPY --chown=airflow:root dags/ ./dags/
