from motor.motor_asyncio import AsyncIOMotorDatabase

from py_nyc.web.data_access.models.listing import Listing


class ListingService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.listing_collection = db.get_collection('listings')

    async def create(self, listing: Listing) -> Listing:
        return await listing.create()

    async def get_by_id(self, id: str):
        return await Listing.get(id)
