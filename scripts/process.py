import pandas as pd
from datetime import datetime


def process_data(data):
    print(data.keys())
    # Check if the data contains the expected keys
    if "hourly" not in data or "time" not in data["hourly"]:
        raise ValueError("Invalid data format: 'hourly' or 'time' key missing")

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["hourly"]["time"]),
        "temperature": data["hourly"]["temperature_2m"],
        "windspeed": data["hourly"]["windspeed_10m"],
        "rain": data["hourly"]["rain"]
    })
    now = datetime.now()
    # ensure proper datetime format
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # keep only rows where timestamp is in the past or present
    df = df[df["timestamp"] <= now]

    return df
