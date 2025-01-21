from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.data_access.models.listing import Plate


class PlateService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.plate_collection = db.get_collection('plates')

    async def create(self, plate: Plate):
        return await plate.create()
