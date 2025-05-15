from prophet import Prophet


def train_prophet(df, feature_name):
    model = Prophet()
    model.fit(df.rename(columns={feature_name: "y"}))
    return model


def train_all_weather_models(df):
    temp_model = train_prophet(df[["ds", "temperature"]].copy(), "temperature")
    rain_model = train_prophet(df[["ds", "rain"]].copy(), "rain")
    wind_model = train_prophet(df[["ds", "windspeed"]].copy(), "windspeed")
    return temp_model, rain_model, wind_model
