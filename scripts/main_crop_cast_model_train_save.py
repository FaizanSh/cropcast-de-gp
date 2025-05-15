import importlib
import Kaggle_dataset_read
from Kaggle_dataset_read import get_data_from_kaggle_file
from kaggle_model_training_pipeline import train_and_evaluate_models

importlib.reload(Kaggle_dataset_read)

X_train, X_test, y_train, y_test = get_data_from_kaggle_file()

# Assuming you already have X_train, X_test, y_train, y_test prepared
train_and_evaluate_models(
    X_train, X_test, y_train, y_test, 
    min_layers=1, 
    max_layers=1)
	