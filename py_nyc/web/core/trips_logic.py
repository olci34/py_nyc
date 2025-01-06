from datetime import datetime
from py_nyc.web.data_access.models.trip import Trip
from py_nyc.web.data_access.services.trip_service import TripService


class TripsLogic:
    def __init__(self, trip_service: TripService):
        self.trip_service = trip_service

    # def get_trips(self) -> list[Trip]:
    #     trips: list[Trip] = self.trip_service.get_all()
    #     serialized_trips = [Trip.from_mongo(trip) for trip in trips]
    #     return serialized_trips

    async def get_density_between(self, start_date: datetime, end_date: datetime, start_hr: int, end_hr: int):
        density = await self.trip_service.get_density_between(
            start_date, end_date, start_hr, end_hr)
        print(len(density))
        return density

    async def get_trip(self, id: str):
        return await self.trip_service.get_by_id(id)
