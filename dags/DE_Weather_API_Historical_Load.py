from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from utils.notification_module import notify_fail


VENV_DIR = Variable.get("VENV_DIR_Model")
SCRIPTS_DIR = Variable.get("SCRIPTS_DIR")
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
    dag_id="DE_Weather_API_Historical_Load",
    description="One off historical backfill using main_historical.py",
    schedule_interval=None,  # trigger manually
    catchup=False,
    default_args=_default_args(),
    tags=["historical", "pipeline"],
) as historical_main_dag:

    BashOperator(
        task_id="run_main_historical",
        bash_command=f"{activate} && python {os.path.join(SCRIPTS_DIR, 'main_historical.py')}",
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        on_failure_callback=notify_fail,
    )