from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from py_nyc.web.data_access.models.trip import Trip


class TripService:
    def __init__(self, database: AsyncIOMotorClient):
        self.trips_collection = database["trips"]

    async def get_by_id(self, id: str) -> Trip | None:
        return await Trip.get(id)

    async def get_density_between(self, start_date: datetime, end_date: datetime, start_hr: int, end_hr: int):
        pipeline = [
            {
                "$match": {
                    "request_datetime": {
                        "$gte": start_date,
                        "$lte": end_date,
                    },
                    "$expr": {
                        "$and": [
                            {
                                "$gte": [
                                    {"$hour": "$request_datetime"},
                                    start_hr,
                                ]
                            },
                            {
                                "$lte": [
                                    {"$hour": "$request_datetime"},
                                    end_hr,
                                ]
                            },
                        ]
                    },
                }
            },
            {
                "$group": {
                    "_id": "$pickup_location_id",
                    "trip_count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "loc_id": "$_id",
                    "trip_count": 1,
                }
            },
        ]

        return await Trip.aggregate(pipeline).to_list()
