from py_nyc.web.data_access.models.listing import Listing
from py_nyc.web.data_access.services.listing_service import ListingService


class ListingsLogic:
    def __init__(self, listing_service: ListingService):
        self.listing_service = listing_service

    async def get_by_id(self, id):
        return await self.listing_service.get_by_id(id)

    async def create_listing(self, listing: Listing):
        return await self.listing_service.create(listing)
