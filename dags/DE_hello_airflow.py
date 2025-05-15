from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from utils.notification_module import notify_fail, notify_failure_processing

def say_hello(**kwargs):
    notify_failure_processing(
        function_name="hello_airflow",
        value="Hello, Faizan! Airflow works locally 🚀",
        qualifier="hello_airflow",
        result="Hello, Faizan! Airflow works locally 🚀",
        context=kwargs,
    )
    print("Hello, Faizan! Airflow works locally 🚀")

with DAG(
    dag_id='DE_hello_airflow',
    start_date=datetime(2024, 4, 27),
    schedule_interval=None,
    catchup=False,
) as dag:
    PythonOperator(
        task_id='say_hello_task',
        python_callable=say_hello,
        on_failure_callback=notify_fail,
    )

