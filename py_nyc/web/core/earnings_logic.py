from datetime import datetime
from typing import List
from py_nyc.web.core.models import TripEarning
from py_nyc.web.external.nyc_open_data_api import get_earnings_data


class EarningsLogic:
    def get_earnings(self, start_date: datetime, end_date: datetime) -> List[TripEarning]:
        earnings_data = get_earnings_data(start_date, end_date)

        resp: List[TripEarning] = []
        for data in earnings_data:
            resp.append(TripEarning(
                total_driver_pay=float(data['total_driver_pay']),
                trip_count=int(data['trip_count']),
                pickup_date=datetime.strptime(
                    data['pickup_date'], "%Y-%m-%dT%H:%M:%S.%f"),
                pickup_hour=int(data['pickup_hour'])
            ))

        return resp
