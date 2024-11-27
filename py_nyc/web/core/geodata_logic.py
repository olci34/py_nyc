from datetime import datetime, timedelta
import json
from starlette import status
from typing import List, Dict
from py_nyc.web.external.nyc_open_data_api import get_trip_data


class GeoDataLogic:
    def get_trips_within(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """
        Returns the number of pick ups in a given date_time and hour_span.

        Parameters
        ----------
        start_date : datetime

        end_date : datetime

        Returns
        -------
        List[List[int]]
          Each list item represents **[pickup_location_id, number_of_pickups]**

        Examples
        --------
        >>> get_trips_within('2024-11-04T15:30:00Z', '2024-10-04T15:30:00Z')
        [[201, 40], [113, 33]]

        """

        resp = get_trip_data(start_date, end_date)

        if resp.status_code == status.HTTP_200_OK:
            trip_list: Dict[str, str] = json.loads(
                resp.content.decode("utf-8"))

            loc_density: Dict[str, int] = {}
            for trip in list(trip_list):
                pulocationid = trip["pulocationid"]
                if pulocationid in loc_density:
                    raise Exception(f"Duplicate location ids found.")

                loc_density[pulocationid] = int(trip["count_pulocationid"])

            return loc_density
        else:
            raise Exception(f"Something went wrong. {resp.status_code}")
