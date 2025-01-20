from datetime import datetime
from typing import List
from py_nyc.web.core.models import TripDensity, TripEarningSoQL
from py_nyc.web.external.nyc_open_data_api import get_density_soda, get_earnings_soda


class TripService:

    def get_density_between(self, from_date: datetime, to_date: datetime, start_hr: int, end_hr: int) -> List[TripDensity]:
        return get_density_soda(from_date, to_date, start_hr, end_hr)

    def get_earnings_data(start_date: datetime, end_date: datetime) -> List[TripEarningSoQL]:
        return get_earnings_soda(start_date, end_date)
