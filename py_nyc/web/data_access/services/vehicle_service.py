from motor.motor_asyncio import AsyncIOMotorDatabase

from py_nyc.web.data_access.models.listing import Vehicle


class VehicleService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.vehicle_collection = db.get_collection('vehicles')

    async def create(self, vehicle: Vehicle):
        return await vehicle.create()
