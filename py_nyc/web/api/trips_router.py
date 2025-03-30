from datetime import datetime
from fastapi import APIRouter, Request
from py_nyc.web.core.trips_logic import TripsLogic
from py_nyc.web.data_access.services.trip_service import TripDensity
from py_nyc.web.dependencies import TripsLogicDep

trips_router = APIRouter(prefix="/trips")


@trips_router.get("/density")
def get_density(startDate: datetime, endDate: datetime, startTime: int, endTime: int, trips_logic: TripsLogicDep) -> list[TripDensity]:
    res = trips_logic.get_density(startDate, endDate, startTime, endTime)
    return res
