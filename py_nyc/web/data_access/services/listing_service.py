from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.api.schemas import ListingSearchParams
from py_nyc.web.data_access.models.listing import Listing, ListingsResponse


class ListingService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.listing_collection = db.get_collection('listings')

    async def create(self, listing: Listing) -> Listing:
        return await listing.create()

    async def get_by_id(self, id: str):
        return await Listing.get(id)

    async def get_listings(self, offset: int, limit: int, search: ListingSearchParams) -> ListingsResponse:
        query = {}
        if search:
            if search.make:
                query["item.make"] = {"$regex": search.make, "$options": "i"}
            if search.model:
                query["item.model"] = {"$regex": search.model, "$options": "i"}
            if search.minYear:
                query["item.year"] = {"$gte": search.minYear}
            if search.maxYear:
                query.setdefault("item.year", {}).update({"$lte": search.maxYear})
            if search.mileageRange:
                try:
                    min_mileage, max_mileage = map(float, search.mileageRange.split("-"))
                    query["item.mileage"] = {"$gte": min_mileage, "$lte": max_mileage}
                except (ValueError, AttributeError):
                    pass
        listings = await Listing.find(query).skip(offset).limit(limit).to_list()
        total = await Listing.find(query).count()

        return ListingsResponse(listings=listings, total=total)
