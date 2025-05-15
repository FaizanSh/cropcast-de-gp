def insert_data(engine, table_name, df):
    df.to_sql(table_name, engine, index=False,
              if_exists='replace', method="multi", chunksize=10000)
