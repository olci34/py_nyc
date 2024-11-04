from datetime import datetime, timedelta
from fastapi import APIRouter, Request
import json
from starlette import status
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from py_nyc.web.api.schemas import ListTripSchema, LocDensitySchema, TripSchema
from py_nyc.web.external.nyc_open_data_api import get_trip_data

router = APIRouter()
templates = Jinja2Templates(directory="./py_nyc/web/templates")


@router.get("/home", response_model=LocDensitySchema)
def get_trips(date: str):
    req_date = datetime.fromisoformat(date)
    from_date = req_date - timedelta(hours=2)
    to_date = req_date + timedelta(hours=2)

    resp = get_trip_data(from_date, to_date)

    if resp.status_code == status.HTTP_200_OK:
        trip_list = json.loads(resp.content.decode("utf-8"))
        loc_density = {}
        for trip in list(trip_list):
            pulocationid = int(trip["pulocationid"])
            if pulocationid in loc_density:
                loc_density[pulocationid] += 1
            else:
                loc_density[pulocationid] = 1

        sorted_density = sorted(loc_density.items(),
                                key=lambda item: item[1], reverse=True)
        return {"density": sorted_density}
    else:
        print(resp)


@router.get("/index", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
