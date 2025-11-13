from datetime import datetime
from typing import List
from starlette import status
import json
import requests
from sodapy import Socrata
from py_nyc.web.core.models import TripEarningSoQL
from py_nyc.web.data_access.services.trip_service import TripDensity
from py_nyc.web.core.config import get_settings

# TODO: Exploit @lru_cache(maxsize=20) for caching results
def get_density_soda(from_date: datetime, to_date: datetime, start_hr: int, end_hr: int) -> List[TripDensity]:
    settings = get_settings()  # Cached via @lru_cache
    client = Socrata("data.cityofnewyork.us", settings.nyc_open_data_app_token, timeout=120)
    query = f"""
        SELECT COUNT(pulocationid) AS density, pulocationid AS location_id 
        WHERE request_datetime >= '{from_date.strftime('%Y-%m-%dT%H:%M:%S.000')}' and request_datetime < '{to_date.strftime('%Y-%m-%dT%H:%M:%S.000')}' and date_extract_hh(request_datetime) between {start_hr} and {end_hr} 
        GROUP BY pulocationid"""
    res = client.get('u253-aew4', query=query)

    return res


def get_earnings_soda(start_date: datetime, end_date: datetime) -> List[TripEarningSoQL]:
    settings = get_settings()  # Cached via @lru_cache
    baseUrl = "https://data.cityofnewyork.us/resource/u253-aew4.json"
    query = f"SELECT date_trunc_ymd(pickup_datetime) AS pickup_date, date_extract_hh(pickup_datetime) AS pickup_hour, SUM(driver_pay) AS total_driver_pay, COUNT(*) AS trip_count WHERE pickup_datetime >= '{start_date.isoformat()}' AND pickup_datetime < '{end_date.isoformat()}' GROUP BY pickup_date, pickup_hour"
    url = f"{baseUrl}?$query={query}"
    headers = {"X-App-Token": settings.nyc_open_data_app_token}

    resp = requests.get(url, headers=headers)
    data = resp.content.decode('utf-8')

    if resp.status_code is not status.HTTP_200_OK:
        raise Exception(
            f"Something went wrong. Status Code: {resp.status_code}. {data}")

    return json.loads(data)
