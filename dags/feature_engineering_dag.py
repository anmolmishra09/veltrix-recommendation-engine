"""
Feature engineering DAG for the recommendation pipeline.
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
    'feature_engineering_dag',
    default_args=default_args,
    description='Generate features from processed data',
    schedule_interval=timedelta(hours=1),
)

# Task to generate user features
generate_user_features = BashOperator(
    task_id='generate_user_features',
    bash_command='spark-submit --master spark://spark-master:7077 /pipelines/features/generate_user_features.py',
    dag=dag,
)

# Task to generate product features
generate_product_features = BashOperator(
    task_id='generate_product_features',
    bash_command='spark-submit --master spark://spark-master:7077 /pipelines/features/generate_product_features.py',
    dag=dag,
)

# Task to generate interaction features (if needed)
generate_interaction_features = BashOperator(
    task_id='generate_interaction_features',
    bash_command='spark-submit --master spark://spark-master:7077 /pipelines/features/interaction_features.py',
    dag=dag,
)

# Set dependencies
[generate_user_features, generate_product_features] >> generate_interaction_features