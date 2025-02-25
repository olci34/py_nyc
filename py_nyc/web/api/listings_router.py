from typing import Optional, Union
from fastapi import APIRouter, Query, Request
from py_nyc.web.api.models.create_listing_request import CreateListingRequest
from py_nyc.web.api.schemas import ListingSearchParams
from py_nyc.web.core.listings_logic import ListingsLogic
from py_nyc.web.core.plates_logic import PlatesLogic
from py_nyc.web.core.vehicles_logic import VehiclesLogic
from py_nyc.web.data_access.models.listing import Listing, ListingCategory, ListingsResponse, Plate, Vehicle
from py_nyc.web.utils.listing_mapper import map_listing_response_to_listing


listings_router = APIRouter(prefix="/listings")


@listings_router.post("/", response_model=Listing)
async def create_listing(create: CreateListingRequest, req: Request):
    listings_logic: ListingsLogic = req.app.state.listings_logic
    vehicles_logic: VehiclesLogic = req.app.state.vehicles_logic
    plates_logic: PlatesLogic = req.app.state.plates_logic
    item: Union[Optional[Vehicle], Optional[Plate]] = None

    if create.listing_category is ListingCategory.Vehicle:
        item = await vehicles_logic.create(create.item)
    elif create.listing_category is ListingCategory.Plate:
        item = await plates_logic.create(create.item)

    listing = map_listing_response_to_listing(create)
    listing.item = item
    res = await listings_logic.create_listing(listing)
    print(res.item)
    res.item = item
    return res


@listings_router.get("/", response_model=ListingsResponse)
async def get_listings(req: Request,
                       page: int = Query(1, ge=1, description="Page number"),
                       per_page: int = Query(
                           20, ge=1, description="Number of items per page"),
                        q: Optional[str] = Query(None, description="Search query in JSON format")):
    listings_logic: ListingsLogic = req.app.state.listings_logic
    search = ListingSearchParams.from_query_string(q)
    print('ROITER', search)
    res = await listings_logic.get_listings(page, per_page, search)
    return res
