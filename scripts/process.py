import pandas as pd


def process_data(data):
    print(data.keys())
    # Check if the data contains the expected keys
    if "hourly" not in data or "time" not in data["hourly"]:
        raise ValueError("Invalid data format: 'hourly' or 'time' key missing")
    # check first 10 rows of the data
    # print(data["hourly"]["time"][:10])
    # print(data["hourly"]["temperature_2m"][:10])
    # print(data["hourly"]["wind_speed_10m"][:10])
    # print(data["hourly"]["rain"][:10])
    # Convert the data into a DataFrame
    return pd.DataFrame({
        "timestamp": pd.to_datetime(data["hourly"]["time"]),
        "temperature": data["hourly"]["temperature_2m"],
        "windspeed": data["hourly"]["windspeed_10m"],
        "rain": data["hourly"]["rain"]
    })
