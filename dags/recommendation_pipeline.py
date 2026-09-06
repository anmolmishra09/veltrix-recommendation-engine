"""
Airflow DAG for the recommendation pipeline.
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
    'recommendation_pipeline',
    default_args=default_args,
    description='A pipeline to generate features and train models for the recommendation system',
    schedule_interval=timedelta(days=1),
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

# Task to train embedding model
train_embedding_model = BashOperator(
    task_id='train_embedding_model',
    bash_command='python /pipelines/training/train_embedding_model.py',
    dag=dag,
)

# Task to train ranking model
train_ranking_model = BashOperator(
    task_id='train_ranking_model',
    bash_command='python /pipelines/training/train_ranking_model.py',
    dag=dag,
)

# Set task dependencies
[generate_user_features, generate_product_features] >> train_embedding_model >> train_ranking_model