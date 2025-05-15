import boto3
import pandas as pd
import io
from config_loader import get_aws_credentials, get_postgres_uri

get_aws_credentials = get_aws_credentials()
def download_to_local_kaggle(key, filename):

    # Initialize S3 client
    # s3 = boto3.client('s3')
    s3 = boto3.client(
    's3',
    aws_access_key_id=get_aws_credentials['aws_access_key_id'],
    aws_secret_access_key=get_aws_credentials['aws_secret_access_key'],
    region_name=get_aws_credentials['region_name']
    )
    bucket_name = 'cropcast'  # Replace with your bucket name
    s3_key = key  # S3 key for your log file


    # Fetch the log file from S3
    obj = s3.get_object(Bucket=bucket_name, Key=s3_key)
    log_data = obj['Body'].read()
    df = pd.read_csv(io.BytesIO(log_data))
    print(df.head())
    print(df.columns)
    #df['timestamp'] = pd.to_datetime(df['timestamp'])
    #df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', dayfirst=False)


    # Keep last 20 predictions
    # df = df.tail(20)

    df.to_csv(filename, index=False)

    return None
keys = ['forecasts/rainfall_forecast.csv', 'forecasts/wind_forecast.csv', 'forecasts/temperature_forecast.csv']
filename = ['rainfall_forecast.csv', 'wind_forecast.csv', 'temperature_forecast.csv']
for i,j in zip(keys,filename):
    download_to_local_kaggle(i,j)