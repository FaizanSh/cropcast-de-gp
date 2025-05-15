import os
from datetime import datetime
import pandas as pd
from config_loader import get_aws_credentials, get_postgres_uri

DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "database-1.c0z8is86qvzm.us-east-1.rds.amazonaws.com"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DBNAME", "postgres")
}

LATITUDE = 31.5204
LONGITUDE = 74.3587
TABLE_NAME = "weather_history"
N_YEARS_AGO = 3

# Get current date (year, month, day)
current_date = pd.Timestamp.today().date()  # removes time, keeps date only

# Date 3 years back from current_date
three_years_back = current_date - pd.DateOffset(years=3)

YEAR = 3
START_YEAR = current_date.replace(year=current_date.year - 3)
END_YEAR = pd.Timestamp.today().date()

# Database configuration
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "database-1.c0z8is86qvzm.us-east-1.rds.amazonaws.com")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DBNAME", "postgres")

# S3 configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
REGION_NAME = os.getenv("REGION_NAME")
