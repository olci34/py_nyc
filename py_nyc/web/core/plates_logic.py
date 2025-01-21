from py_nyc.web.data_access.models.listing import Plate
from py_nyc.web.data_access.services.plate_service import PlateService


class PlatesLogic:
    def __init__(self, plate_service: PlateService):
        self.plate_service = plate_service

    async def create(self, plate: Plate):
        return self.plate_service.create(plate)
