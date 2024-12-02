from datetime import datetime
from urllib.parse import urlencode
import requests
import os


def get_density_data(from_date: datetime, to_date: datetime):
    APP_TOKEN = os.environ.get("NYC_OPEN_DATA_APP_TOKEN")
    baseUrl = "https://data.cityofnewyork.us/resource/u253-aew4.json"
    query = {
        "$select": "count(pulocationid), pulocationid",
        "$where": f"request_datetime between '{from_date.isoformat()}' and '{to_date.isoformat()}'",
        "$group": "pulocationid"
    }
    url = f"{baseUrl}?{urlencode(query)}"

    headers = {"X-App-Token": APP_TOKEN}
    resp = requests.get(url, headers=headers)

    return resp
