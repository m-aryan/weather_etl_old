import requests
import pandas as pd
from datetime import date, timedelta


def fetch_weather(lat, lon, city):
    today = date.today()
    start_date = today - timedelta(days=5)

    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}"
        f"&longitude={lon}"
        f"&start_date={start_date}"
        f"&end_date={today}"
        f"&hourly=temperature_2m,precipitation"
    )

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data["hourly"])
    df["city"] = city
    return df
