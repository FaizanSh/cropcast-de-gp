from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from utils.notification_module import notify_fail

VENV_DIR = Variable.get("VENV_DIR")
SCRIPTS_DIR = Variable.get("SCRIPTS_DIR")
PRODUCER_PATH = os.path.join(SCRIPTS_DIR, "iot_crop_producer.py")

activate = f"source {VENV_DIR}/bin/activate"


def _default_args(**extra):
    base = {
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "start_date": datetime(2025, 5, 14),
    }
    base.update(extra)
    return base
	
with DAG(
    dag_id="DE_IoT_Crop_Producer_Kafka",
    description="Generates synthetic IoT crop events and pushes to Kafka",
    schedule_interval="@hourly",  # tweak as required
    catchup=False,
    max_active_runs=1,
    default_args=_default_args(),
    tags=["farm", "kafka", "producer"],
) as producer_dag:

    run_producer = BashOperator(
        task_id="run_iot_crop_producer",
        bash_command=f"{activate} && python {PRODUCER_PATH}",
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        on_failure_callback=notify_fail
    )
