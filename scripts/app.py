
#####################################################################################################################################################
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import boto3
import io
from sqlalchemy import create_engine
from config_loader import get_aws_credentials

# AWS S3 configuration
aws_credentials = get_aws_credentials()
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_credentials["aws_access_key_id"],
    aws_secret_access_key=aws_credentials["aws_secret_access_key"],
    region_name=aws_credentials["region_name"]
)
bucket_name = 'cropcast'

def load_data_from_s3(file_key):
    """
    Load data from S3 bucket
    """
    try:
        # Get the object from S3
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        # Read CSV content
        return pd.read_csv(io.BytesIO(obj['Body'].read()))
    except Exception as e:
        st.error(f"Error loading {file_key} from S3: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error



def connect_to_postgres(db_user, db_password, db_host, db_port, db_name):
    """Create a connection to PostgreSQL database.
    
    Args:
        db_user (str): Database username
        db_password (str): Database password
        db_host (str): Database host address
        db_port (str): Database port
        db_name (str): Database name
    
    Returns:
        sqlalchemy.engine.Engine: Database connection engine
    """
    engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
    print("Connected to PostgreSQL database")
    # Check connection
    # try:
    #     with engine.connect() as connection:
    #         connection.execute("SELECT 1;")  # Simple query to check connection
    #         print("Connection successful")
    # except Exception as e:
    #     print(f"Connection failed: {e}")
    #     raise
    # finally:
    #     print("Connection closed")
    return engine


def fetch_weather_data(engine, query="SELECT * FROM weather_history;"):
    """Fetch weather data from the database.
    
    Args:
        engine (sqlalchemy.engine.Engine): Database connection engine
        query (str, optional): SQL query to fetch data. Defaults to "SELECT * FROM weather_history;".
    
    Returns:
        pandas.DataFrame: Fetched weather data
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


def preprocess_weather_data(df):
    """Preprocess the weather data for forecasting.
    
    Args:
        df (pandas.DataFrame): Raw weather data
    
    Returns:
        pandas.DataFrame: Processed weather data
    """
    df['ds'] = pd.to_datetime(df['timestamp'])
    df = df.fillna(df.mean(numeric_only=True))
    return df

def fetching_from_postgres():
    """Fetch and preprocess weather data from PostgreSQL database.
    
    Returns:
        pandas.DataFrame: Processed weather data
    """
    db_user = "postgres"
    db_password = "LumsDE1122"
    db_host = "database-1.c0z8is86qvzm.us-east-1.rds.amazonaws.com"
    db_port = "5432"
    db_name = "postgres"

    engine = connect_to_postgres(db_user, db_password, db_host, db_port, db_name)
    df = fetch_weather_data(engine)
    
    print(df.head())
    
    df = preprocess_weather_data(df)
    
    print(f"Cleansed data with correct date/time format and zero nulls: {df.head()}")
    return df

def weatherAPI_Streamlit():
    st_autorefresh(interval=400000, limit=None, key="weather_refresh")
    # Load data
    with st.spinner('Loading data from AWS S3...'):
        df = fetching_from_postgres()

        temp_forecast = pd.read_csv('temperature_forecast.csv')
 
        rain_forecast = pd.read_csv('rainfall_forecast.csv')
      
        wind_forecast = pd.read_csv('wind_forecast.csv')
        pass

    # Function to filter data based on gap
    def filter_by_gap(dataframe, gap):
        return dataframe.iloc[::gap]

    # Set page configuration
    #st.set_page_config(page_title="Weather Forecast", layout="wide")

    # Create figure with dark theme
    fig = go.Figure()

    # --- Temperature (Actual & Predicted) ---
    fig.add_trace(go.Scatter(x=df['ds'], y=df['temperature'],
                            mode='lines', name='Actual Temperature (°C)',
                            visible=True, line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=temp_forecast['ds'], y=temp_forecast['temperature'],
                            mode='lines', name='Predicted Temperature (°C)',
                            visible=True, line=dict(color='white')))

    # --- Rain (Actual & Predicted) ---
    fig.add_trace(go.Scatter(x=df['ds'], y=df['rain'],
                            mode='lines', name='Actual Rainfall (mm)',
                            visible=False, line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=rain_forecast['ds'], y=rain_forecast['rainfall'],
                            mode='lines', name='Predicted Rainfall (mm)',
                            visible=False, line=dict(color='white')))

    # --- Wind Speed (Actual & Predicted) ---
    fig.add_trace(go.Scatter(x=df['ds'], y=df['windspeed'],
                            mode='lines', name='Actual Wind Speed (m/s)',
                            visible=False, line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=wind_forecast['ds'], y=wind_forecast['wind_speed'],
                            mode='lines', name='Predicted Wind Speed (m/s)',
                            visible=False, line=dict(color='white')))

    # Create slider steps
    steps = []
    max_gap = 24  # Maximum gap value (adjust based on your data)

    for gap in range(1, max_gap + 1):
        df_sampled = filter_by_gap(df, gap)
        temp_forecast_sampled = filter_by_gap(temp_forecast, gap)
        rain_forecast_sampled = filter_by_gap(rain_forecast, gap)
        wind_forecast_sampled = filter_by_gap(wind_forecast, gap)

        step = dict(
            method='update',
            args=[
                {
                    'x': [
                        df_sampled['ds'], temp_forecast_sampled['ds'],
                        df_sampled['ds'], rain_forecast_sampled['ds'],
                        df_sampled['ds'], wind_forecast_sampled['ds']
                    ],
                    'y': [
                        df_sampled['temperature'], temp_forecast_sampled['temperature'],
                        df_sampled['rain'], rain_forecast_sampled['rainfall'],
                        df_sampled['windspeed'], wind_forecast_sampled['wind_speed']
                    ]
                },
                {'title': f'Weather Forecast: Actual vs Predicted (Every {gap} Hours)'}
            ],
            label=f'{gap}h'
        )
        steps.append(step)

    # Dropdown buttons for switching between metrics
    dropdown_buttons = [
        dict(label="Temperature",
            method="update",
            args=[{"visible": [True, True, False, False, False, False]},
                {"yaxis": {"title": "Temperature (°C)"}}]),
        dict(label="Rain",
            method="update",
            args=[{"visible": [False, False, True, True, False, False]},
                {"yaxis": {"title": "Rainfall (mm)"}}]),
        dict(label="Wind Speed",
            method="update",
            args=[{"visible": [False, False, False, False, True, True]},
                {"yaxis": {"title": "Wind Speed (m/s)"}}]),
    ]

    # Update layout to include both dropdown and slider
    fig.update_layout(
        updatemenus=[dict(
            active=0,
            buttons=dropdown_buttons,
            direction="down",
            showactive=True,
            x=1.1,
            yanchor="bottom",
            font=dict(color="white"),
            bgcolor="rgba(50, 50, 50, 0.7)",
            bordercolor="white"
        )],
        sliders=[dict(
            active=0,
            currentvalue={"prefix": "Sampling Interval: ", "font": {"color": "white"}},
            pad={"t": 50},
            steps=steps,
            bgcolor="#444",
            activebgcolor="#888",
            bordercolor="white",
            tickcolor="white"
        )]
    )

    # General Layout - dark theme
    fig.update_layout(
        title={"text": "Weather Forecast: Actual vs Predicted", "font": {"color": "white", "size": 24}},
        xaxis_title={"text": "Date and Time", "font": {"color": "white"}},
        yaxis_title={"text": "Temperature (°C)", "font": {"color": "white"}},
        # width=1600, 
        height=800,
        margin=dict(l=50, r=50, t=100, b=100),
        plot_bgcolor="black", paper_bgcolor="black",
        font=dict(color="white"),
        xaxis=dict(gridcolor="rgba(255, 255, 255, 0.2)", zerolinecolor="white", tickfont=dict(color="white")),
        yaxis=dict(gridcolor="rgba(255, 255, 255, 0.2)", zerolinecolor="white", tickfont=dict(color="white")),
        legend=dict(font=dict(color="white"), bgcolor="rgba(50, 50, 50, 0.7)")
    )

    # Display plot using Streamlit
    # st.write(fig )

    st.plotly_chart(fig, use_container_width=True)

    if __name__ == "__main__":
        weatherAPI_Streamlit()

