"""
Training DAG for the recommendation pipeline.
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
    'training_dag',
    default_args=default_args,
    description='Train recommendation models',
    schedule_interval=timedelta(days=1),
)

# Task to generate training dataset
generate_training_dataset = BashOperator(
    task_id='generate_training_dataset',
    bash_command='spark-submit --master spark://spark-master:7077 /pipelines/features/training_dataset.py',
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

# Task to train candidate generation models (if needed)
train_candidate_model = BashOperator(
    task_id='train_candidate_model',
    bash_command='python /pipelines/training/train_candidate_model.py',
    dag=dag,
)

# Set dependencies
generate_training_dataset >> [train_embedding_model, train_ranking_model, train_candidate_model]