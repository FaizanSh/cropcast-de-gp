import streamlit as st
import pandas as pd
import plotly.express as px
import os
import boto3
import io 
import time
from streamlit_autorefresh import st_autorefresh
from sqlalchemy import create_engine
from config_loader import get_aws_credentials

credentials = get_aws_credentials()
#LOG_PATH = "inference_log_kaggle.csv"
s3 = boto3.client(
    's3',
    aws_access_key_id=credentials["aws_access_key_id"],
    aws_secret_access_key=credentials["aws_secret_access_key"],
    region_name=credentials["region_name"]
)
bucket_name = 'cropcast'

def load_data_from_s3(file_key):
    """
    Load data from S3 bucket
    """
    try:
        # Get the object from S3
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        # Read CSV content
        return pd.read_csv(io.BytesIO(obj['Body'].read()))
    except Exception as e:
        st.error(f"Error loading {file_key} from S3: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
    

def connect_to_postgres(db_user, db_password, db_host, db_port, db_name):
    """Create a connection to PostgreSQL database.
    
    Args:
        db_user (str): Database username
        db_password (str): Database password
        db_host (str): Database host address
        db_port (str): Database port
        db_name (str): Database name
    
    Returns:
        sqlalchemy.engine.Engine: Database connection engine
    """
    engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
    return engine


def fetch_weather_data(engine, query="SELECT processed_at, predicted_yield FROM farm_metrics ORDER BY processed_at DESC LIMIT 20"):
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        return pd.DataFrame()

def preprocess_weather_data(df):
    """Preprocess the weather data for forecasting.
    
    Args:
        df (pandas.DataFrame): Raw weather data
    
    Returns:
        pandas.DataFrame: Processed weather data
    """
    df['ds'] = pd.to_datetime(df['processed_at'])
    df = df.fillna(df.mean(numeric_only=True))
    return df

def fetching_from_postgres():
    """Fetch and preprocess weather data from PostgreSQL database.
    
    Returns:
        pandas.DataFrame: Processed weather data
    """
    # Database connection parameters

    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "database-1.c0z8is86qvzm.us-east-1.rds.amazonaws.com")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "postgres")

    engine = connect_to_postgres(db_user, db_password, db_host, db_port, db_name)
    df = fetch_weather_data(engine)
    
    print(df.head())
    
    df = preprocess_weather_data(df)
    
    print(f"Cleansed data with correct date/time format and zero nulls: {df.head()}")
    return df

#
    



def kaggle_streamlit():
    st_autorefresh(interval=10000, limit=None, key="kaggle_refresh")
    ####
    # AWS S3 configuration
   

    # Set up the Streamlit app
    #st.set_page_config(page_title="Prediction Monitor", layout="wide")
    ###
    # REFRESH_INTERVAL = 3  # seconds
    st.title("📈 Live Prediction Tracker")
    # Auto-refresh block
    # if "last_refresh" not in st.session_state:
    #     st.session_state.last_refresh = time.time()
    # elif time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    #     st.session_state.last_refresh = time.time()
    #     st.rerun()

    try:
        # Fetch the log file from S3
        # obj = s3.get_object(Bucket=bucket_name, Key=s3_key)
        # log_data = obj['Body'].read()

        # # Load the log data into a DataFrame
        # df = pd.read_csv(io.BytesIO(log_data))

    
        # df = pd.read_csv("df_kaggle_inference.csv")
        df = fetching_from_postgres()
        # df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Keep last 20 predictions
        # df = df.tail(20)


        # Display the data
        st.dataframe(df)

        # Line chart using Plotly
        fig = px.line(df, x="processed_at", y="predicted_yield", markers=True,
                    title="Last 20 Predictions Over Time")
        fig.update_layout(
            title='Real-time Crop Yield Predictions (Last 20 days)',
            xaxis_title='Timestamp',
            yaxis_title='Predicted crop yield in Tons per Hectare',
            height=500,
            margin=dict(l=0, r=0, t=30, b=0),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Optionally, show data table
        with st.expander("Show raw prediction data"):
            st.dataframe(df[::-1], use_container_width=True)


    # except s3.exceptions.NoSuchKey:
    #     st.warning("No predictions have been made yet.")
    except Exception as e:
        st.error(f"Failed to fetch or read S3 log: {e}")
