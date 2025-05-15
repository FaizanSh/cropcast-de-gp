from config import DB_CONFIG, LATITUDE, LONGITUDE, TABLE_NAME, START_YEAR, END_YEAR
from db import get_engine, recreate_table
from fetch import fetch_weather_data_API
from process import process_data
from insert import insert_data


def main():
    engine = get_engine(DB_CONFIG)
    # recreate_table(engine, TABLE_NAME)
    print(f" Fetching data...")
    data = fetch_weather_data_API(latitude=LATITUDE, longitude=LONGITUDE, n_days=1)
    print(f" Processing data for...")
    df = process_data(data)
    insert_data(engine, TABLE_NAME, df)
    print(f" Inserted data ")


if __name__ == "__main__":
    main()