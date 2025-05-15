import pandas as pd
import numpy as np
import os
import boto3
import io
import logging
from config_loader import get_aws_credentials
# Load AWS credentials from environment variables

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS credentials and configuration
aws_credentials = get_aws_credentials()
aws_access_key = aws_credentials['aws_access_key_id']
aws_secret_key = aws_credentials['aws_secret_access_key']
bucket_name = 'cropcast'
region_name = aws_credentials['region_name']
s3_key = 'models/inference_log.csv'

# Create S3 client with explicit credentials
def get_s3_client():
    """
    Create and configure S3 client with explicit credentials
    
    Returns:
        boto3.client: Configured S3 client
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region_name
        )
        logger.info("Successfully created S3 client with explicit credentials")
        return s3_client
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        return None

def save_to_s3_log(s3_client, row, bucket_name, s3_key, result):
    """
    Save the inference results to S3
    
    Args:
        s3_client: boto3 S3 client
        row (pd.DataFrame): DataFrame row with inference results
        bucket_name (str): S3 bucket name
        s3_key (str): S3 object key
        result: The prediction result to return
        
    Returns:
        The prediction result
    """
    try:
        logger.info(f"Attempting to save inference log to s3://{bucket_name}/{s3_key}")
        
        # Try to get existing file
        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            log_df = pd.read_csv(io.BytesIO(obj['Body'].read()))
            logger.info(f"Found existing log file with {len(log_df)} records")
            log_df = pd.concat([log_df, row], ignore_index=True)
        except s3_client.exceptions.NoSuchKey:
            logger.info("Log file doesn't exist yet, creating new one")
            log_df = row  # File doesn't exist yet
        except Exception as e:
            logger.error(f"Failed to fetch or read S3 log: {e}")
            raise RuntimeError(f"Failed to fetch or read S3 log: {e}")

        # Save back to S3
        csv_buffer = io.StringIO()
        log_df.to_csv(csv_buffer, index=False)
        s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=csv_buffer.getvalue())
        logger.info(f"Successfully saved inference log with {len(log_df)} records")

        return result
    except Exception as e:
        logger.error(f"Error saving to S3 log: {e}")
        # Return the result anyway even if logging fails
        return result

def inference(pipeline, array, s3_key="models/inference_log.csv"):
    """
    Run inference on the given array using the provided pipeline,
    and log the time and result to a DataFrame.

    Args:
        pipeline: The trained pipeline with a .predict() method.
        array (np.ndarray): The input array for inference.
        s3_key (str): S3 key for the CSV file to log inference results.

    Returns:
        np.ndarray: The prediction result.
    """
    try:
        # Get current timestamp
        time = pd.Timestamp.now()
        logger.info(f"Starting inference at {time}")

        # Perform inference
        result = pipeline.predict(array)
        logger.info(f"Inference completed, result shape: {result.shape if hasattr(result, 'shape') else 'scalar'}")
        
        # Prepare result row
        row = pd.DataFrame({
            'timestamp': [time],
            'prediction': [str(result)]  # Convert to string to ensure it can be stored in CSV
        })
        
        # Get S3 client
        s3_client = get_s3_client()
        if s3_client is None:
            logger.error("Failed to create S3 client, skipping log saving")
            return result
            
        # Fix backslash in s3_key if present (Windows path separator issue)
        s3_key = s3_key.replace('\\', '/')
        
        # Save to S3 log
        result = save_to_s3_log(s3_client, row, bucket_name, s3_key, result)
        
        return result
    except Exception as e:
        logger.error(f"Error in inference function: {e}")
        # Re-raise to ensure caller knows there was a problem
        raise





