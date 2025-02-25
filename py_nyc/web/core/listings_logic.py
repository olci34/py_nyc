from py_nyc.web.api.schemas import ListingSearchParams
from py_nyc.web.data_access.models.listing import Listing, ListingResponse
from py_nyc.web.data_access.services.listing_service import ListingService


class ListingsLogic:
    def __init__(self, listing_service: ListingService):
        self.listing_service = listing_service

    async def get_by_id(self, id):
        return await self.listing_service.get_by_id(id)

    async def create_listing(self, listing: Listing):
        return await self.listing_service.create(listing)

    async def get_listings(self, page: int, limit: int, search: ListingSearchParams) -> ListingResponse:
        offset = (page - 1) * limit
        return await self.listing_service.get_listings(offset, limit, search)
