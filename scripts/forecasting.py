import pandas as pd
import boto3
import io
from config_loader import get_aws_credentials, get_postgres_uri
# AWS S3 configuration
aws_credentials = get_aws_credentials()
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_credentials["aws_access_key_id"],
    aws_secret_access_key=aws_credentials["aws_secret_access_key"],
    region_name=aws_credentials["region_name"]
)
bucket_name = 'cropcast'

def generate_future_dataframe(last_timestamp, periods=24*7, freq='h'):
    """
    Generate a dataframe with future timestamps for forecasting
    """
    future = pd.date_range(
        start=last_timestamp + pd.Timedelta(hours=1),
        periods=periods,
        freq=freq
    )
    return pd.DataFrame({'ds': future})



def generate_forecasts(models, future_df):
    """
    Generate forecasts using the provided models and save to S3
    """
    temp_model, rain_model, wind_model = models
    
    # Generate forecasts
    temp_forecast = temp_model.predict(future_df)['yhat']
    rain_forecast = rain_model.predict(future_df)['yhat']
    wind_forecast = wind_model.predict(future_df)['yhat']
    print(type(temp_forecast))
    print(type(rain_forecast))
    print(type(wind_forecast))
    print(len(temp_forecast))
    print(len(rain_forecast))
    print(len(wind_forecast))
    print(temp_forecast.head())
    # Create result dataframes with timestamps
    temp_df = pd.DataFrame({'timestamp': future_df['ds'], 'temperature': temp_forecast})
    rain_df = pd.DataFrame({'timestamp': future_df['ds'], 'rainfall': rain_forecast})
    wind_df = pd.DataFrame({'timestamp': future_df['ds'], 'wind_speed': wind_forecast})
    print ("*")
    print(temp_df.head())
    
    # Save directly to S3
    save_to_s3(temp_df, 'temperature_forecast.csv')
    save_to_s3(rain_df, 'rainfall_forecast.csv')
    save_to_s3(wind_df, 'wind_forecast.csv')
    
    return temp_forecast, rain_forecast, wind_forecast

def save_to_s3(df, filename):
    """
    Save a dataframe directly to S3
    """
    try:
        # Convert dataframe to CSV in memory
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        # Upload to S3, overwriting any existing file
        s3.put_object(
            Bucket=bucket_name,
            Key=f'forecasts/{filename}',
            Body=csv_buffer.getvalue()
        )
        
    except Exception as e:
        print(f"Error saving {filename} to S3: {e}")


# Example usage (commented out, would be replaced with actual usage)
# if __name__ == "__main__":
#     last_timestamp = pd.Timestamp('2023-01-01')
#     future_df = generate_future_dataframe(last_timestamp)
#     models = (temp_model, rain_model, wind_model)  # Replace with actual models
#     temp_forecast, rain_forecast, wind_forecast = generate_forecasts(models, future_df)