from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, AWS_ACCESS_KEY, AWS_SECRET_KEY, BUCKET_NAME, REGION_NAME
from db_connection import connect_to_postgres
from data_fetch import fetch_weather_data_POSTGRES
from data_preprocess import preprocess_weather_data
from model_training import train_all_weather_models
from model_management import save_models
from forecasting import generate_future_dataframe, generate_forecasts
from save_results import save_to_csv
# from plotting import generate_weather_plot
from s3_upload import upload_to_s3
from IPython.display import clear_output


def run_weather_forecast_pipeline(forecast_days=7, save_csv=True, plot_results=True, save_models_to_disk=True, upload_to_s3_bucket=True):
    engine = connect_to_postgres(
        DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
    df = fetch_weather_data_POSTGRES(engine)
    df = preprocess_weather_data(df)

    temp_model, rain_model, wind_model = train_all_weather_models(df)

    if save_models_to_disk:
        save_models(temp_model, rain_model, wind_model)

    last_timestamp = df['ds'].max()
    future = generate_future_dataframe(
        last_timestamp, periods=24*forecast_days)

    temp_forecast, rain_forecast, wind_forecast = generate_forecasts(
        (temp_model, rain_model, wind_model),
        future
    )

    if save_csv:
        save_to_csv(df, temp_forecast, rain_forecast, wind_forecast)

    if upload_to_s3_bucket:
        model_files = {
            'temp_model_weather_api.pkl': 'models/temp_model_weather_api.pkl',
            'rain_model_weather_api.pkl': 'models/rain_model_weather_api.pkl',
            'wind_model_weather_api.pkl': 'models/wind_model_weather_api.pkl'
        }

        upload_to_s3(model_files, BUCKET_NAME, AWS_ACCESS_KEY,
                     AWS_SECRET_KEY, REGION_NAME)

    # if plot_results:
    #     clear_output()
    #     generate_weather_plot(df, temp_forecast, rain_forecast, wind_forecast)

    return df, temp_forecast, rain_forecast, wind_forecast


if __name__ == "__main__":
    run_weather_forecast_pipeline(
        forecast_days=7,
        save_csv=True,
        plot_results=True,
        save_models_to_disk=True,
        upload_to_s3_bucket=True
    )
