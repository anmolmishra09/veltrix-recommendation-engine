"""
Evaluation DAG for the recommendation pipeline.
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
    'evaluation_dag',
    default_args=default_args,
    description='Evaluate recommendation models',
    schedule_interval=timedelta(days=1),
)

# Task to evaluate candidate generation
evaluate_candidates = BashOperator(
    task_id='evaluate_candidates',
    bash_command='python /pipelines/evaluation/evaluate_candidates.py',
    dag=dag,
)

# Task to evaluate ranking
evaluate_ranking = BashOperator(
    task_id='evaluate_ranking',
    bash_command='python /pipelines/evaluation/evaluate_ranking.py',
    dag=dag,
)

# Task to generate evaluation report
generate_report = BashOperator(
    task_id='generate_report',
    bash_command='python /pipelines/evaluation/generate_report.py',
    dag=dag,
)

# Set dependencies
[evaluate_candidates, evaluate_ranking] >> generate_report