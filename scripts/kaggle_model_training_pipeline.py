import numpy as np
import tensorflow as tf
import joblib
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.metrics import MeanAbsoluteError
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, RegressorMixin
import os
import boto3
import logging
from config_loader import get_aws_credentials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS S3 configuration - using boto3 best practices for credentials
def get_s3_client():
    """
    Create and configure S3 client using best practices
    
    Returns:
        boto3.client: Configured S3 client
    """
    try:
        # Better to use AWS credentials from environment variables or credential files
        # rather than hardcoding them
        aws_credentials = get_aws_credentials()
        s3_client = boto3.client(
            's3',
            region_name=aws_credentials["region_name"],
            aws_access_key_id=aws_credentials["aws_access_key_id"],
            aws_secret_access_key=aws_credentials["aws_secret_access_key"]
        )
        return s3_client
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        return None

# Define bucket name
BUCKET_NAME = 'cropcast'

class KerasModelWrapper(BaseEstimator, RegressorMixin):
    def __init__(self, hidden_layers=2, epochs=50, batch_size=32, learning_rate=0.01):
        """
        Custom Keras Model Wrapper for scikit-learn compatibility
        
        Args:
            hidden_layers (int): Number of hidden layers
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
            learning_rate (float): Learning rate for Adam optimizer
        """
        
        self.hidden_layers = hidden_layers
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.model = None

    def build_model(self, input_dim):
        """
        Build Keras neural network model
        
        Args:
            input_dim (int): Number of input features
        
        Returns:
            tensorflow.keras.Model: Compiled neural network model
        """
        model = Sequential()
        model.add(Input(shape=(input_dim,)))
        for _ in range(self.hidden_layers):
            model.add(Dense(64, activation='relu'))
        model.add(Dense(1))
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss=MeanSquaredError(),
            metrics=[MeanAbsoluteError()]
        )
        return model

    def fit(self, X, y):
        """
        Fit the model to training data
        
        Args:
            X (numpy.ndarray): Training features
            y (numpy.ndarray): Training target
        
        Returns:
            self: Fitted model
        """
        self.model = self.build_model(X.shape[1])
        self.model.fit(
            X, y, 
            epochs=self.epochs, 
            batch_size=self.batch_size, 
            verbose=0, 
            validation_split=0.2
        )
        return self

    def predict(self, X):
        """
        Make predictions
        
        Args:
            X (numpy.ndarray): Input features
        
        Returns:
            numpy.ndarray: Predictions
        """
        return self.model.predict(X).flatten()

def upload_file_to_s3(local_path, s3_key):
    """
    Upload a file to S3 with proper error handling
    
    Args:
        local_path (str): Path to local file
        s3_key (str): Destination key in S3 bucket
    
    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        logger.info(f"Uploading {local_path} to s3://{BUCKET_NAME}/{s3_key}")
        
        # Check if file exists locally
        if not os.path.exists(local_path):
            logger.error(f"Local file {local_path} does not exist")
            return False
            
        # Get S3 client
        s3_client = get_s3_client()
        if s3_client is None:
            logger.error("Failed to create S3 client")
            return False
            
        # Upload file
        s3_client.upload_file(local_path, BUCKET_NAME, s3_key)
        
        # Verify upload by checking if object exists
        try:
            s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_key)
            logger.info(f"Successfully uploaded to s3://{BUCKET_NAME}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to verify upload: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error uploading file to S3: {e}")
        return False

def train_and_evaluate_models(X_train, X_test, y_train, y_test, min_layers=1, max_layers=5, save_dir='./models/'):
    """
    Train and evaluate neural network models with varying numbers of hidden layers
    
    Args:
        X_train (numpy.ndarray): Training feature data
        X_test (numpy.ndarray): Testing feature data
        y_train (numpy.ndarray): Training target data
        y_test (numpy.ndarray): Testing target data
        min_layers (int, optional): Minimum number of hidden layers. Defaults to 1.
        max_layers (int, optional): Maximum number of hidden layers. Defaults to 5.
        save_dir (str, optional): Directory to save models. Defaults to './models/'.
    
    Returns:
        dict: Dictionary containing upload status and best model information
    """
    logger.info("Starting model training and evaluation")
    
    # Create save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Early stopping to prevent overfitting
    early_stopping = EarlyStopping(
        monitor='val_loss', 
        patience=10, 
        restore_best_weights=True
    )

    def create_model(hidden_layers):
        """
        Create a neural network model with specified number of hidden layers
        
        Args:
            hidden_layers (int): Number of hidden layers to create
        
        Returns:
            tuple: Compiled and trained model with its training history
        """
        model = Sequential()
        model.add(Input(shape=(X_train.shape[1],)))
        
        # Add hidden layers
        for _ in range(hidden_layers):
            model.add(Dense(64, activation='relu'))
        
        model.add(Dense(1))  
        
        # Compilation
        model.compile(
            optimizer=Adam(learning_rate=0.01), 
            loss='mse', 
            metrics=['mae']
        )
        
        # Training
        history = model.fit(
            X_train, y_train, 
            validation_split=0.2, 
            epochs=50, 
            batch_size=32, 
            verbose=0,
            callbacks=[early_stopping]
        )
        
        return model, history

    # Store results for different layer configurations
    results = {}

    for layers in range(min_layers, max_layers + 1):
        # Train model
        logger.info(f"Training model with {layers} hidden layers")
        model, history = create_model(layers)

        # Predictions and evaluation
        y_pred = model.predict(X_test).flatten()
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Store results
        results[layers] = {
            'model': model, 
            'history': history, 
            'mse': mse, 
            'r2': r2
        }
        
        logger.info(f"Model with {layers} hidden layers: MSE={mse:.4f}, R²={r2:.4f}")

    # Find best model based on minimum MSE
    best_layers = min(results, key=lambda x: results[x]['mse'])
    best_model = results[best_layers]['model']
    best_mse = results[best_layers]['mse']
    best_r2 = results[best_layers]['r2']

    logger.info(f"Best Model: {best_layers} layers, MSE={best_mse:.4f}, R²={best_r2:.4f}")

    # Create and fit pipeline with the best model configuration
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    pipeline = Pipeline([
        ('scaler', scaler),
        ('model', KerasModelWrapper(hidden_layers=best_layers))
    ])

    # Fit the pipeline
    logger.info("Fitting pipeline with the best model configuration...")
    pipeline.fit(X_train, y_train)
    logger.info("Pipeline fitted.")

    # Define file paths
    scaler_file = os.path.join(save_dir, 'scaler_kaggle_1.pkl')
    model_file = os.path.join(save_dir, 'model_kaggle_1.h5')
    
    # S3 keys (destination paths)
    scaler_key = 'models/scaler_kaggle_1.pkl'
    model_key = 'models/model_kaggle_1.h5'

    # Save models locally
    logger.info(f"Saving scaler to {scaler_file}")
    joblib.dump(pipeline.named_steps['scaler'], scaler_file)
    
    logger.info(f"Saving model to {model_file}")
    pipeline.named_steps['model'].model.save(model_file)

    # Upload to S3
    upload_results = {
        'scaler_uploaded': upload_file_to_s3(scaler_file, scaler_key),
        'model_uploaded': upload_file_to_s3(model_file, model_key),
        'best_layers': best_layers,
        'best_mse': best_mse,
        'best_r2': best_r2
    }
    
    # Log upload results
    if upload_results['scaler_uploaded'] and upload_results['model_uploaded']:
        logger.info("All models successfully uploaded to S3")
    else:
        logger.warning("Some models failed to upload to S3")
        
    # Append to inference log in S3 if needed
    try:
        log_data = f"{best_layers},{best_mse},{best_r2}\n"
        s3_client = get_s3_client()
        if s3_client:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key='models/inference_log.csv',
                Body=log_data,
                ACL='private'
            )
            logger.info("Updated inference log in S3")
    except Exception as e:
        logger.error(f"Failed to update inference log: {e}")

    return upload_results

# Optional: Allow script to be run directly for testing
if __name__ == "__main__":
    # For testing, you would need to provide X_train, X_test, y_train, y_test
    # results = train_and_evaluate_models(X_train, X_test, y_train, y_test, save_dir='./models/')
    # print(f"Upload results: {results}")
    logger.info("Script executed directly - no data provided for training")