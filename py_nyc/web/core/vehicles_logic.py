from py_nyc.web.data_access.models.listing import Vehicle
from py_nyc.web.data_access.services.vehicle_service import VehicleService


class VehiclesLogic:
    def __init__(self, vehicle_service: VehicleService):
        self.vehicle_service = vehicle_service

    async def create(self, vehicle: Vehicle):
        return await self.vehicle_service.create(vehicle)
