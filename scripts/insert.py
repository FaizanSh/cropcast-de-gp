from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import Table, MetaData
import pandas as pd


def insert_data(engine, table_name, df):
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    print(f"DataFrame to insert: {len(df)} rows")
    print(df.head())

    if df.empty:
        print("DataFrame is empty after processing.")
        return

    metadata = MetaData()
    metadata.reflect(bind=engine)
    table = metadata.tables[table_name]

    rows = df.to_dict(orient='records')

    stmt = insert(table).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=['timestamp'],
        set_={
            'temperature': stmt.excluded.temperature,
            'windspeed': stmt.excluded.windspeed,
            'rain': stmt.excluded.rain,
        }
    )

    with engine.begin() as conn:
        conn.execute(stmt)

    print(
        f"Inserted/Updated {len(rows)} rows (NULLs included where needed).")
