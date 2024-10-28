from datetime import datetime
import requests
import os


def get_trip_data(from_date: datetime, to_date: datetime):
    APP_TOKEN = os.environ.get("NYC_OPEN_DATA_APP_TOKEN")
    url = f"https://data.cityofnewyork.us/resource/u253-aew4.json?$where=request_datetime > '{from_date.isoformat()}' and request_datetime > '{to_date.isoformat()}'"
    headers = {"X-App-Token": APP_TOKEN}
    resp = requests.get(url, headers=headers)

    return resp
