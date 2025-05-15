from sqlalchemy import create_engine, text


def get_engine(config):
    return create_engine(
        f"postgresql+psycopg2://{config['user']}:{config['password']}@"
        f"{config['host']}:{config['port']}/{config['dbname']}"
    )


def recreate_table(engine, table_name):
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name};"))
        conn.execute(text(f"""
            CREATE TABLE {table_name} (
                timestamp TIMESTAMP PRIMARY KEY,
                temperature FLOAT,
                windspeed FLOAT,
                rain FLOAT
            );
        """))
        conn.commit()
