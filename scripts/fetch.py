import requests

from datetime import datetime, timedelta
def fetch_weather_data_API(latitude, longitude, n_days=365*3): #365*
    # Get date range using pandas
    today = datetime.today()
    start = today - timedelta(days= n_days)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.strftime('%Y-%m-%d'),
        "end_date": today.strftime('%Y-%m-%d'),
        "hourly": "temperature_2m,rain,windspeed_10m",
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    data = response.json()
    # print(data)
    return data