from datetime import datetime
from fastapi import APIRouter
from py_nyc.web.core.earnings_logic import EarningsLogic
from py_nyc.web.core.geodata_logic import GeoDataLogic
from py_nyc.web.core.models import TripDensity, TripEarning
from typing import List

router = APIRouter()

geodata_handler = GeoDataLogic()
earnings_handler = EarningsLogic()


@router.get("/density", response_model=List[TripDensity])
def get_density(startDate: datetime, endDate: datetime):
    return geodata_handler.get_density_within(startDate, endDate)


@router.get("/earnings", response_model=List[TripEarning])
def get_earnings(startDate: datetime, endDate: datetime):
    return earnings_handler.get_earnings(startDate, endDate)
