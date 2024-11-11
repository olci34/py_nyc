from typing import Annotated
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Tuple


class TripSchema(BaseModel):
    driver_pay: float
    base_passenger_fare: float
    trip_miles: float
    trip_time: int
    request_datetime: datetime
    pulocationid: int
    dolocationid: int


class ListTripSchema(BaseModel):
    trips: List[TripSchema]


class LocDensitySchema(BaseModel):
    """
    Pickup location density
    """
    density: List[Tuple[int, int]]
