from datetime import datetime
from py_nyc.web.data_access.services.trip_service import TripDensity, TripService


class TripsLogic:
    def __init__(self, trip_service: TripService):
        self.trip_service = trip_service

    def get_density(self, start_date: datetime, end_date: datetime, start_hr: int, end_hr: int) -> list[TripDensity]:
        current_date = start_date
        res = {}
        divisor = ((end_date - start_date).days + 1) * (end_hr - start_hr)

        density = self.trip_service.get_density_between(
            current_date, end_date, start_hr, end_hr)

        for trip_density in density:
            if trip_density['location_id'] in res:
                res[trip_density['location_id']
                    ] += int(trip_density['density']) / divisor
            else:
                res[trip_density['location_id']] = int(
                    trip_density['density']) / divisor

        return [TripDensity(location_id=location_id, density=round(density)) for location_id, density in res.items()]
