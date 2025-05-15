#!/bin/bash

# Activate the virtual environment
source ~/airflow_local/venv/bin/activate

# Set AIRFLOW_HOME (if not already exported in bashrc)
export AIRFLOW_HOME=~/airflow_local/airflow

# Kill any previous airflow webserver or scheduler processes
echo "Stopping existing Airflow processes..."
pkill -f "airflow webserver"
pkill -f "airflow scheduler"

sleep 2  # Give them a moment to shut down

# Start webserver using nohup
echo "Starting Airflow Webserver..."
nohup airflow webserver --port 8080 > "$AIRFLOW_HOME/webserver.log" 2>&1 &

# Start scheduler using nohup
echo "Starting Airflow Scheduler..."
nohup airflow scheduler > "$AIRFLOW_HOME/scheduler.log" 2>&1 &

echo "✅ Airflow is now running. Access it at http://localhost:8080"

