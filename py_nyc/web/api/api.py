from datetime import datetime
from fastapi import APIRouter
from py_nyc.web.core.geodata_logic import GeoDataLogic
from py_nyc.web.core.models import TripDensity
from typing import List

router = APIRouter()

geodata_handler = GeoDataLogic()


@router.get("/density", response_model=List[TripDensity])
def get_density(startDate: datetime, endDate: datetime):
    return geodata_handler.get_density_within(startDate, endDate)
