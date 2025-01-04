from py_nyc.web.data_access.config import trips_collection
from py_nyc.web.data_access.models.trip import Trip


class TripsLogic:
    def get_trips(self) -> list[Trip]:
        trips: list[Trip] = list(trips_collection.find())
        serialized_trips = [Trip.from_mongo(trip) for trip in trips]
        return serialized_trips
