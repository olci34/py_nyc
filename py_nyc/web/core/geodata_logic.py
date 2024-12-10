from datetime import datetime
import json
from starlette import status
from typing import List, Dict
from py_nyc.web.core.models import TripDensity
from py_nyc.web.external.nyc_open_data_api import get_density_data


class GeoDataLogic:
    def get_density_within(self, start_date: datetime, end_date: datetime) -> List[TripDensity]:
        """
        Returns the number of trips between given start_date and end_date datetimes.

        Parameters
        ----------
        start_date : datetime

        end_date : datetime

        Returns
        -------
        List[TripDensity]

        [ { location_id: int, denstiy; int }, ... ]

        Examples
        --------
        >>> get_trips_within('2024-11-04T15:30:00', '2024-10-04T15:30:00')
        [
            {location_id: 33, density: 27},
            {location_id: 224, density: 120}
        ]

        """

        trip_list = get_density_data(start_date, end_date)
        resp: List[TripDensity] = []

        for trip in trip_list:
            resp.append(TripDensity(
                location_id=trip['pulocationid'], density=trip['count_pulocationid']))

        return resp
