"""
Ingestion DAG for the recommendation pipeline.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 9, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ingestion_dag',
    default_args=default_args,
    description='Ingest events from Kafka to data lake',
    schedule_interval=timedelta(minutes=10),
)

# Task to run the event consumer (in a real scenario, this would be a long-running service)
# For batch ingestion, we might have a script that consumes from Kafka and writes to S3/data lake
ingest_events = BashOperator(
    task_id='ingest_events',
    bash_command='python /pipelines/ingestion/kafka_to_s3.py',  # We'll create this script later
    dag=dag,
)