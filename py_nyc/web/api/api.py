from datetime import datetime
from fastapi import APIRouter, Request
from py_nyc.web.core.trips_logic import TripsLogic
from py_nyc.web.data_access.services.trip_service import TripDensity

router = APIRouter(prefix="/trips", dependencies=[])


@router.get("/density")
def get_density(startDate: datetime, endDate: datetime, startTime: int, endTime: int, req: Request) -> list[TripDensity]:
    trips_logic: TripsLogic = req.app.state.trips_logic
    res = trips_logic.get_density(startDate, endDate, startTime, endTime)
    return res
