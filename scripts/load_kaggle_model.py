import joblib
import numpy as np
import os
import logging
from tensorflow.keras.models import load_model
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.metrics import MeanAbsoluteError
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.pipeline import Pipeline
import boto3
import botocore.exceptions
from config_loader import get_aws_credentials
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
credentials = get_aws_credentials()
# Better AWS configuration - prefer environment variables for credentials
BUCKET_NAME = 'cropcast'
AWS_ACCESS_KEY = credentials["aws_access_key_id"]
AWS_SECRET_KEY = credentials["aws_secret_access_key"]
AWS_REGION = credentials["region_name"]
SCALER_S3_KEY = 'models/scalar_kaggle_1.pkl'
MODEL_S3_KEY = 'models/model_kaggle_1.h5'
LOCAL_SCALER_PATH = 'scalar_kaggle_1.pkl'
LOCAL_MODEL_PATH = 'model_kaggle_1.h5'

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
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        logger.info("Successfully created S3 client with explicit credentials")
        return s3_client
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        return None

class KerasModelWrapper(BaseEstimator, RegressorMixin):
    def __init__(self):
        self.model = None

    def fit(self, X, y):
        return self  # No retraining

    def predict(self, X):
        if self.model is None:
            raise ValueError("Model is not loaded. Cannot make predictions.")
        return self.model.predict(X).flatten()

def check_file_exists_in_s3(s3_client, bucket, key):
    """
    Check if a file exists in S3
    
    Args:
        s3_client: boto3 S3 client
        bucket (str): Bucket name
        key (str): Object key in S3
        
    Returns:
        bool: True if file exists, False otherwise
    """
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        logger.info(f"File exists in S3: s3://{bucket}/{key}")
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.error(f"File does not exist in S3: s3://{bucket}/{key}")
        else:
            logger.error(f"Error checking if file exists: {e}")
        return False

def list_objects_in_directory(s3_client, bucket, prefix):
    """
    List objects in an S3 directory for debugging
    
    Args:
        s3_client: boto3 S3 client
        bucket (str): Bucket name
        prefix (str): Directory prefix
        
    Returns:
        list: List of object keys
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' in response:
            object_keys = [obj['Key'] for obj in response['Contents']]
            logger.info(f"Found {len(object_keys)} objects in s3://{bucket}/{prefix}")
            for key in object_keys:
                logger.info(f"  - {key}")
            return object_keys
        else:
            logger.warning(f"No objects found in s3://{bucket}/{prefix}")
            return []
            
    except Exception as e:
        logger.error(f"Error listing objects in S3: {e}")
        return []

def download_from_s3(s3_client, bucket, key, local_path):
    """
    Download a file from S3 with proper error handling
    
    Args:
        s3_client: boto3 S3 client
        bucket (str): Bucket name
        key (str): Object key in S3
        local_path (str): Local path to save the file
        
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        # First check if file exists
        if not check_file_exists_in_s3(s3_client, bucket, key):
            return False
            
        # Create directory if it doesn't exist
        directory = os.path.dirname(local_path)
        if directory:  # Only try to create if there's actually a directory component
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Download file
        logger.info(f"Downloading s3://{bucket}/{key} to {local_path}")
        s3_client.download_file(Bucket=bucket, Key=key, Filename=local_path)
        
        # Verify download
        if os.path.exists(local_path):
            logger.info(f"Successfully downloaded to {local_path}")
            return True
        else:
            logger.error(f"Download completed but file not found at {local_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error downloading file from S3: {e}")
        return False

def load_prediction_model():
    """
    Load the prediction model and scaler from S3
    
    Returns:
        Pipeline or None: Loaded pipeline or None if loading failed
    """
    try:
        logger.info("Starting model loading process")
        
        # Get S3 client
        s3_client = get_s3_client()
        if s3_client is None:
            raise RuntimeError("Failed to create S3 client")
        
        # Check bucket access
        try:
            s3_client.head_bucket(Bucket=BUCKET_NAME)
            logger.info(f"Successfully connected to bucket: {BUCKET_NAME}")
        except Exception as e:
            logger.error(f"Cannot access bucket {BUCKET_NAME}: {e}")
            # List available buckets for debugging
            response = s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            logger.info(f"Available buckets: {buckets}")
            raise RuntimeError(f"Cannot access bucket {BUCKET_NAME}")

        # List objects in models directory for debugging
        list_objects_in_directory(s3_client, BUCKET_NAME, 'models/')
        
        # Check if files exist before downloading
        scaler_exists = check_file_exists_in_s3(s3_client, BUCKET_NAME, SCALER_S3_KEY)
        model_exists = check_file_exists_in_s3(s3_client, BUCKET_NAME, MODEL_S3_KEY)
        
        if not scaler_exists or not model_exists:
            raise FileNotFoundError("One or more required files not found in S3")
        
        # Download files
        scaler_downloaded = download_from_s3(s3_client, BUCKET_NAME, SCALER_S3_KEY, LOCAL_SCALER_PATH)
        model_downloaded = download_from_s3(s3_client, BUCKET_NAME, MODEL_S3_KEY, LOCAL_MODEL_PATH)
        
        if not scaler_downloaded or not model_downloaded:
            raise RuntimeError("Failed to download one or more files from S3")
        
        # Load scaler
        logger.info(f"Loading scaler from {LOCAL_SCALER_PATH}")
        loaded_scaler = joblib.load(LOCAL_SCALER_PATH)
        
        # Load Keras model
        logger.info(f"Loading model from {LOCAL_MODEL_PATH}")
        loaded_keras_model = load_model(LOCAL_MODEL_PATH, custom_objects={
            'mean_squared_error': MeanSquaredError(),
            'mean_absolute_error': MeanAbsoluteError()
        })

        # Create model wrapper
        logger.info("Creating model wrapper")
        wrapper = KerasModelWrapper()
        wrapper.model = loaded_keras_model

        # Assemble pipeline
        logger.info("Assembling pipeline")
        pipeline = Pipeline([
            ('scaler', loaded_scaler),
            ('model', wrapper)
        ])

        logger.info("Model and scaler successfully loaded")
        return pipeline

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading model or scaler: {e}")
        return None

# def inference(numpy_array):
#     """
#     Predict using the loaded model and scaler.

#     Args:
#         numpy_array (numpy.ndarray): Input data for prediction.

#     Returns:
#         numpy.ndarray: Predicted values.
#     """
#     pipeline = load_prediction_model()
#     if pipeline is not None:
#         try:
#             logger.info(f"Making prediction with input shape: {numpy_array.shape}")
#             predictions = pipeline.predict(numpy_array)
#             logger.info("Prediction successful")
#             return predictions
#         except Exception as e:
#             error_msg = f"Prediction failed: {e}"
#             logger.error(error_msg)
#             raise RuntimeError(error_msg)
#     else:
#         error_msg = "Model pipeline could not be loaded. Cannot predict."
#         logger.error(error_msg)
#         raise RuntimeError(error_msg)

# Run script manually for testing
if __name__ == "__main__":
    # Test with dummy data
    dummy_input = np.array([[1, 2, 3, 4, 5]])  # Adjust dimensions to match your model's input
    
    try:
        # Test S3 connectivity first
        s3_client = get_s3_client()
        if s3_client:
            logger.info("S3 client created successfully")
            
            # Test bucket access
            try:
                s3_client.head_bucket(Bucket=BUCKET_NAME)
                logger.info(f"Bucket {BUCKET_NAME} exists and is accessible")
            except Exception as e:
                logger.error(f"Cannot access bucket {BUCKET_NAME}: {e}")
                
            # List all buckets
            response = s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            logger.info(f"Available buckets: {buckets}")
            
            # List files in the models directory
            list_objects_in_directory(s3_client, BUCKET_NAME, 'models/')
        
        # Try to make a prediction
        logger.info("Attempting to make prediction...")
        #preds = inference(dummy_input)
        #logger.info(f"Predictions: {preds}")
        
    except Exception as err:
        logger.error(f"Error during prediction: {err}")