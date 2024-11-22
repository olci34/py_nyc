from fastapi import APIRouter, Request
import json
import os
from starlette import status
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from py_nyc.web.core.geodata_logic import GeoDataLogic
from py_nyc.web.core.models import GeoJSONFeature, TaxiZoneGeoJSON
from typing import List

router = APIRouter()
templates = Jinja2Templates(directory="./py_nyc/web/templates")

geodata_handler = GeoDataLogic()


@router.get("/trips", response_model=TaxiZoneGeoJSON)
def get_trips(date: str, hour_span: int):
    print(hour_span)
    trips = geodata_handler.get_trips_within(date, hour_span)
    GEOJSON_FILE_PATH = './py_nyc/web/static/nyc-taxi-zones.geojson'

    try:
        # Read the GeoJSON file
        with open(GEOJSON_FILE_PATH, 'r') as file:
            geojson_data = json.load(file)
            fts: List[GeoJSONFeature] = []
            for geo in geojson_data['features']:
                location_id = geo['properties']['location_id']
                if location_id in trips:
                    geo['properties']['density'] = trips.get(location_id)
                    fts.append(geo)

        res = TaxiZoneGeoJSON(type=geojson_data['type'], features=fts)
        return res
    except FileNotFoundError:
        print("File not found")
    except json.JSONDecodeError:
        print("JSON decoding went wrong.")


@router.get("/index", response_class=HTMLResponse)
def index(request: Request):
    GEOJSON_FILE_PATH = os.path.join("static", "nyc-taxi-zones.geojson")

    try:
        # Read the GeoJSON file
        with open(GEOJSON_FILE_PATH, 'r') as file:
            geojson_data = json.load(file)  # Parse JSON data

    except FileNotFoundError:
        print("File not found")
    except json.JSONDecodeError:
        print("JSON decoding went wron.")

    return templates.TemplateResponse(request=request, name="index.html")
