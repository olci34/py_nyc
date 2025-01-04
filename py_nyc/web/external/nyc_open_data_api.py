from datetime import datetime
from typing import Dict, List
from urllib.parse import urlencode
from starlette import status
import json
import requests
import os

from py_nyc.web.core.models import TripEarningSoQL


def get_density_data(from_date: datetime, to_date: datetime) -> List[Dict[str, str]]:
    APP_TOKEN = os.environ.get("NYC_OPEN_DATA_APP_TOKEN")
    baseUrl = "https://data.cityofnewyork.us/resource/u253-aew4.json"
    query = {
        "$select": "count(pulocationid), pulocationid",
        "$where": f"date_trunc_ymd(request_datetime) between '{from_date.strftime('%Y-%m-%d')}' and '{to_date.strftime('%Y-%m-%d')}' and date_extract_hh(request_datetime) between {from_date.hour} and {to_date.hour}",
        "$group": "pulocationid"
    }
    url = f"{baseUrl}?{urlencode(query)}"
    headers = {"X-App-Token": APP_TOKEN}

    resp = requests.get(url, headers=headers)
    data = resp.content.decode('utf-8')

    if resp.status_code is not status.HTTP_200_OK:
        raise Exception(
            f"Something went wrong. Status Code: {resp.status_code}. {data}")

    return json.loads(data)


def get_earnings_data(start_date: datetime, end_date: datetime) -> List[TripEarningSoQL]:
    APP_TOKEN = os.environ.get("NYC_OPEN_DATA_APP_TOKEN")
    baseUrl = "https://data.cityofnewyork.us/resource/u253-aew4.json"
    query = f"SELECT date_trunc_ymd(pickup_datetime) AS pickup_date, date_extract_hh(pickup_datetime) AS pickup_hour, SUM(driver_pay) AS total_driver_pay, COUNT(*) AS trip_count WHERE pickup_datetime >= '{start_date.isoformat()}' AND pickup_datetime < '{end_date.isoformat()}' GROUP BY pickup_date, pickup_hour"
    url = f"{baseUrl}?$query={query}"
    headers = {"X-App-Token": APP_TOKEN}

    resp = requests.get(url, headers=headers)
    data = resp.content.decode('utf-8')

    if resp.status_code is not status.HTTP_200_OK:
        raise Exception(
            f"Something went wrong. Status Code: {resp.status_code}. {data}")

    return json.loads(data)
