from fastapi import APIRouter, Request
import json
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from py_nyc.web.core.geodata_logic import GeoDataLogic
from py_nyc.web.core.models import TaxiZoneGeoJSON

router = APIRouter()
templates = Jinja2Templates(directory="./py_nyc/web/templates")

geodata_handler = GeoDataLogic()


@router.get("/trips", response_model=TaxiZoneGeoJSON)
def get_trips(date: str):
    sorted_density = geodata_handler.get_trips_within(date, 2)
    hash = set([data[0] for data in sorted_density[:10]])
    GEOJSON_FILE_PATH = './py_nyc/web/static/nyc-taxi-zones.geojson'

    try:
        # Read the GeoJSON file
        with open(GEOJSON_FILE_PATH, 'r') as file:
            geojson_data = json.load(file)
            fts = [
                geo for geo in geojson_data['features'] if geo['properties']['location_id'] in hash
            ]

        res = TaxiZoneGeoJSON(type=geojson_data['type'], features=fts)
        return res
    except FileNotFoundError:
        print("File not found")
    except json.JSONDecodeError:
        print("JSON decoding went wrong.")


@router.get("/index", response_class=HTMLResponse)
def index(request: Request):

    return templates.TemplateResponse(request=request, name="index.html")
