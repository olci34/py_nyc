from dataclasses import dataclass
from datetime import datetime
from pydantic import conint
from pydantic.dataclasses import dataclass as pydantic_dataclass
from typing import Dict, List


@dataclass
class GeoData:
    type: str
    coordinates: List[List[List[List[float]]]]


@dataclass
class TaxiZoneProperties:
    shape_area: float
    objectid: int
    shape_leng: float
    location_id: int
    zone: str
    borough: str
    density: int


@dataclass
class GeoJSONFeature:
    type: str
    properties: TaxiZoneProperties
    geometry: GeoData


@pydantic_dataclass
class TaxiZoneGeoJSON:
    type: str
    features: List[GeoJSONFeature]


@pydantic_dataclass
class TripDensity:
    location_id: int
    density: int


@pydantic_dataclass
class TripEarning:
    trip_count: int
    total_driver_pay: float
    pickup_date: datetime
    pickup_hour: conint(ge=0, le=24)  # type: ignore


@dataclass
class TripEarningSoQL:
    trip_count: str
    total_driver_pay: str
    pickup_date: str
    pickup_hour: str
