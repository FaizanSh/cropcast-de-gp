import boto3
from config_loader import get_aws_credentials

config = get_aws_credentials()
# AWS credentials and S3 info
s3 = boto3.client('s3')
aws_access_key = config["aws_access_key_id"]
aws_secret_key = config["aws_secret_access_key"]
bucket_name = 'cropcast'
region_name = config["region_name"]
s3_key = 'models/crop_yield_data.csv'
local_file_path = r'C:\Users\HP\Desktop\DESKTOP\LUMS\1. SEMESTER 2\DATA ENGINEERING AI 601\PROJECT\Kaggle_complete\crop_yield_data.csv'

# Create S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name
)

# Upload file
s3.upload_file(local_file_path, bucket_name, s3_key)

print("Upload successful.")
