from dataclasses import dataclass
from pydantic.dataclasses import dataclass as pydantic_dataclass
from typing import List


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
