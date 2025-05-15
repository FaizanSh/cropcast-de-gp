def save_to_csv(df, temp_forecast, rain_forecast, wind_forecast, prefix=""):
    df.to_csv(f"{prefix}df.csv", index=False)
    temp_forecast.to_csv(f"{prefix}temp_forecast.csv", index=False)
    rain_forecast.to_csv(f"{prefix}rain_forecast.csv", index=False)
    wind_forecast.to_csv(f"{prefix}wind_forecast.csv", index=False)
