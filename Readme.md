# Step 1
### There is .env.sample file, add your details in it and change it to .env file,
### Place it in scripts folder for your scirpts to work, where you have to paste in your credentials. In case if you have any difficulty, do reach out to us

# Step 2
# Run DLL file dll.sql in your DB

# Step 3
## Kafka Installation Guide [Docker Required]
In the folder where zk-single-kafka.yml exist
Run 
`docker-compose -f zk-single-kafka.yml up -d`
Check if its running
`docker-compose -f zk-single-kafka.yml ps`
exec to create topic
`docker exec -it kafka1 /bin/bash`
`kafka-topics --create --topic farm_predictions --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 testing`

# Step 4
## Environments setup
pip install -r stream_requirements.txt
pip install -r venv_requirements.txt

# Step 5
### below are the DAG in sequential manner they execute the associated Python command in their respective virtual environment - in case if you couldn't enable dags (Installation guide in the end), you can run the scripts in these order

Dag: `DE_Weather_API_Historical_Load.py`
Command: `python main_historical.py`

Dag: `DE_Weather_API_Daily_Load.py`
Command: `python main_daily.py`

Dag: `DE_Weather_API_Prediction.py`
Command: `python run_pipeline.py`

Dag: `DE_IoT_Crop_Historical_Data_Model.py`
Command: `python main_crop_cast_model_train_save.py`

Dag: `DE_IoT_Crop_Producer_Kafka.py`
Command: `python iot_crop_producer.py`

Dag: `DE_IoT_Crop_Consumer_Kafka_Spark_with_Prediction.py`
Command: `spark-submit --packages org.postgresql:postgresql:42.7.3,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5 farm_predictions.py`

# Extra Guide Step for Airflow in Ubuntu Environment

## Airflow installation guide

## Update and Install System Dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv libffi-dev libssl-dev libpq-dev python3-dev gcc

## Create a Virtual Environment
mkdir ~/airflow_local && cd ~/airflow_local
python3 -m venv venv
source venv/bin/activate

## Set Airflow Home
export AIRFLOW_HOME=~/airflow_local/airflow
mkdir -p $AIRFLOW_HOME

### To make this permanent, add to ~/.bashrc
echo "export AIRFLOW_HOME=~/airflow_local/airflow" >> ~/.bashrc

### Install Airflow via pip (with constraints)
AIRFLOW_VERSION=2.8.2
PYTHON_VERSION="$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1-2)"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

## Initialize Airflow DB (using SQLite for now) Default
airflow db init

## Create an Admin User
airflow users create --username admin --firstname Faizan --lastname Ullah --role Admin --email 23030015@lums.edu.pk

## Create dags/ Folder and add copy the dags folder

## Start Webserver and Scheduler
./start_airflow.sh
or

source venv/bin/activate
airflow webserver --port 8080

source venv/bin/activate
airflow scheduler

http://localhost:8080

## Create Variables in Airflow
Example Values
ENVIRONMENT: dev
SCRIPTS_DIR: /home/faizan/airflow_local/scripts
VENV_DIR: /home/faizan/airflow_local/venv
VENV_DIR_Model:	/home/faizan/airflow_local/.stream

## this is a channel posting url - create this variable in airflow too - or create your webhook via teams channel and share add its URL
dev-DE: https://prod-168.westeurope.logic.azure.com:443/workflows/c586bf820dee4790a85ad23be37dc24d/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=wykVRefqXKx9XrqK91g1v5DDiQ20f3v0ZhELee_1-4A
create another virtual environment like .stream and install stream_requirements.txt file