import pandas as pd


def fetch_weather_data_POSTGRES(engine, query="SELECT * FROM weather_history;"):
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df
