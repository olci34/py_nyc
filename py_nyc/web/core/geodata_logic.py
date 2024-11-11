from datetime import datetime, timedelta
import json
from starlette import status
from typing import List
from py_nyc.web.external.nyc_open_data_api import get_trip_data


class GeoDataLogic:
    def get_trips_within(self, date_time: str, hour_span: int) -> List[List]:
        """
        Returns the number of pick ups in a given date_time and hour_span.

        Parameters
        ----------
        date_time : str
          Date string of trips.

        hour_span: int
          Hour window.

        Returns
        -------
        List[List[int]]
          Each list item represents **[pickup_location_id, number_of_pickups]**

        Examples
        --------
        >>> get_trips_within('2024-11-04T15:30:00Z', 2)
        [[201, 40], [113, 33]]

        """
        req_date = datetime.fromisoformat(date_time)
        print(req_date.strftime('%Y-%m-%dT%H:%M:%S%z'))
        from_date = req_date - timedelta(hours=hour_span)
        to_date = req_date + timedelta(hours=hour_span)

        resp = get_trip_data(from_date, to_date)

        if resp.status_code == status.HTTP_200_OK:
            trip_list = json.loads(resp.content.decode("utf-8"))
            loc_density = {}
            for trip in list(trip_list):
                pulocationid = trip["pulocationid"]
                if pulocationid in loc_density:
                    loc_density[pulocationid] += 1
                else:
                    loc_density[pulocationid] = 1

            return sorted(loc_density.items(),
                          key=lambda item: item[1], reverse=True)
        else:
            raise Exception(f"Something went wrong. {resp.status_code}")
