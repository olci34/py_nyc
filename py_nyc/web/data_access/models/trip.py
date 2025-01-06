from datetime import datetime
from typing import Annotated
from beanie import Document, Indexed


class Trip(Document):
    # id: str | None = Field(alias="_id")
    hvfhs_license_num: str
    dispatching_base_num: str
    originating_base_num: str | None
    request_datetime: Annotated[datetime, Indexed()]
    on_scene_datetime: datetime | None
    pickup_datetime: datetime | None
    dropoff_datetime: datetime | None
    pickup_location_id: Annotated[int, Indexed()]
    dropoff_location_id: int | None
    trip_miles: float | None
    trip_time: int | None
    base_passenger_fare: float | None
    tolls: float | None
    bcf: float | None
    sales_tax: float | None
    congestion_surcharge: float | None
    airport_fee: float | None
    tips: float | None
    driver_pay: float | None
    shared_request_flag: str | None
    shared_match_flag: str | None
    access_a_ride_flag: str | None
    wav_request_flag: str | None
    wav_match_flag: str | None

    class Settings:
        name = "trips"

    # @field_validator("id", mode='before')
    # def convert_objectid_to_str(cls, v: Any):
    #     if isinstance(v, ObjectId):
    #         return str(v)
    #     return v

    # def to_mongo(self):
    #     """Convert the Trip model to a dictionary for MongoDB."""
    #     data = self.model_dump(by_alias=True)
    #     if self.id:
    #         data["_id"] = ObjectId(self.id)
    #     return data

    # @staticmethod
    # def from_mongo(data):
    #     """Convert a MongoDB document to a Trip model."""
    #     if data is None:
    #         return None
    #     data["id"] = str(data["_id"])
    #     return Trip(**data)
