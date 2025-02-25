import json
from typing import Annotated, Optional
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

class ListingSearchParams(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    minYear: Optional[int] = None
    maxYear: Optional[int] = None
    mileageRange: Optional[str] = None
    
    @classmethod
    def from_query_string(cls, q: Optional[str] = None) -> 'ListingSearchParams':
        if not q:
            return cls()
        try:
            # Assuming q is a JSON string
            params = json.loads(q)
            return cls(**params)
        except json.JSONDecodeError:
            # If not JSON, return empty params
            return cls()