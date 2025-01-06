from datetime import datetime
from fastapi import APIRouter, Request
from py_nyc.web.core.trips_logic import TripsLogic

router = APIRouter(prefix="/trips", dependencies=[])


@router.get("/density")
async def get_density(startDate: datetime, endDate: datetime, startTime: int, endTime: int, req: Request):
    trips_logic: TripsLogic = req.app.state.trips_logic
    print(startDate, endDate)
    return await trips_logic.get_density_between(startDate, endDate, startTime, endTime)


@router.get("/{id}")
async def get_trip(id: str, req: Request):
    trips_logic: TripsLogic = req.app.state.trips_logic
    print(id)
    return await trips_logic.get_trip(id)
