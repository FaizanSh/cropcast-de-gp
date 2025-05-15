import boto3
import pandas as pd
import io
from config_loader import get_aws_credentials
# AWS S3 configuration
aws_credentials = get_aws_credentials()
def download_to_local_kaggle(se_key):

    # Initialize S3 client
    # s3 = boto3.client('s3')
    s3 = boto3.client(
    's3',
    aws_access_key_id=get_aws_credentials['aws_access_key_id'],
    aws_secret_access_key=get_aws_credentials['aws_secret_access_key'],
    region_name=get_aws_credentials['region_name']
    )
    bucket_name = 'cropcast'  # Replace with your bucket name
    s3_key = se_key  # S3 key for your log file


    # Fetch the log file from S3
    obj = s3.get_object(Bucket=bucket_name, Key=s3_key)
    log_data = obj['Body'].read()
    df = pd.read_csv(io.BytesIO(log_data))
    print(df.head())
    print(df.columns)
    #df['timestamp'] = pd.to_datetime(df['timestamp'])
    #df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', dayfirst=False)


    # Keep last 20 predictions
    df = df.tail(20)

    df.to_csv("df_kaggle_inference.csv", index=False)

    return None

se_key = 'models/inference_log.csv'
download_to_local_kaggle(se_key)