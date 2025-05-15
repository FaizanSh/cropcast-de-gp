import joblib


def save_models(temp_model, rain_model, wind_model, prefix=""):
    joblib.dump(temp_model, f"{prefix}temp_model_weather_api.pkl")
    joblib.dump(rain_model, f"{prefix}rain_model_weather_api.pkl")
    joblib.dump(wind_model, f"{prefix}wind_model_weather_api.pkl")


def load_models(prefix=""):
    temp_model = joblib.load(f"{prefix}temp_model_weather_api.pkl")
    rain_model = joblib.load(f"{prefix}rain_model_weather_api.pkl")
    wind_model = joblib.load(f"{prefix}wind_model_weather_api.pkl")
    return temp_model, rain_model, wind_model
