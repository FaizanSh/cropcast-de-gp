import pandas as pd


def preprocess_weather_data(df):
    df['ds'] = pd.to_datetime(df['timestamp'])
    df = df.fillna(df.mean(numeric_only=True))
    return df
