import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import boto3
import io
from config_loader import get_aws_credentials

aws_credentials = get_aws_credentials()
aws_access_key = aws_credentials['aws_access_key_id']
aws_secret_key = aws_credentials['aws_secret_access_key']
s3 = boto3.client('s3',
                  aws_access_key_id=aws_access_key,
                  aws_secret_access_key=aws_secret_key,
                  region_name=aws_credentials['region_name'])

bucket_name = 'cropcast'
region_name = aws_credentials['region_name']

def get_data_from_kaggle_file():
    '''
    Loads the file of the kaggle saved file and transforms the data into scaled splits for ML
    '''
    aws_credentials = get_aws_credentials()
    aws_access_key = aws_credentials['aws_access_key_id']
    aws_secret_key = aws_credentials['aws_secret_access_key']
    bucket_name = 'cropcast'
    region_name = aws_credentials['region_name']
    
    s3 = boto3.client('s3',
                      aws_access_key_id=aws_access_key,
                      aws_secret_access_key=aws_secret_key,
                      region_name=region_name)

    bucket_name = 'cropcast'
    region_name = aws_credentials['region_name']
    s3_key = 'models/crop_yield_data.csv'

    obj = s3.get_object(Bucket=bucket_name, Key=s3_key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))

    df = df.dropna()  

    for col in ['rainfall_mm', 'soil_quality_index', 'farm_size_hectares', 'sunlight_hours', 'fertilizer_kg']:
        df = df[df[col] > 0]
    X = df.drop('crop_yield', axis=1)
    y = df['crop_yield']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    return X_train, X_test, y_train, y_test