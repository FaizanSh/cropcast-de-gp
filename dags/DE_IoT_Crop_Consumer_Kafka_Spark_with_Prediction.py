from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from utils.notification_module import notify_fail

VENV_DIR = Variable.get("VENV_DIR")
SCRIPTS_DIR = Variable.get("SCRIPTS_DIR")
CONSUMER_PATH = os.path.join(SCRIPTS_DIR, "farm_predictions.py")

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
    dag_id="DE_IoT_Crop_Consumer_Kafka_Spark_with_Prediction",
    description="Aggregates Kafka events, predicts yield, and writes to Postgres",
    schedule_interval="@hourly",  # graceful hourly recycle
    catchup=False,
    max_active_runs=1,
    default_args=_default_args(),
    tags=["farm", "spark", "consumer", "kafka", "prediction", "model"],
) as consumer_dag:

    spark_submit_cmd = (
        f"{activate} && "
        "spark-submit "
        "--conf spark.streaming.stopGracefullyOnShutdown=true "
        "--conf spark.sql.streaming.stopGracefullyOnShutdown=true "
        "--conf spark.sql.streaming.stopTimeout=30s "
        "--packages org.postgresql:postgresql:42.7.3,"
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5 "
        f"{CONSUMER_PATH}"
    )

    run_consumer = BashOperator(
        task_id="run_farm_consumer",
        bash_command=spark_submit_cmd,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        on_failure_callback=notify_fail,
    )