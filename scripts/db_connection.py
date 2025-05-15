from sqlalchemy import create_engine


def connect_to_postgres(db_user, db_password, db_host, db_port, db_name):
    engine = create_engine(
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
    return engine
