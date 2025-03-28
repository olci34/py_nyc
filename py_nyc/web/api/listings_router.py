from typing import Annotated, Optional, Union
from fastapi import APIRouter, Depends, Query
from py_nyc.web.dependencies import ListingsLogicDep, PlatesLogicDep, VehiclesLogicDep
from .models.create_listing_request import CreateListingRequest
from .schemas import ListingSearchParams
from ..data_access.models.listing import Listing, ListingCategory, ListingsResponse, Plate, Vehicle
from py_nyc.web.utils.listing_mapper import map_listing_response_to_listing
from py_nyc.web.utils.auth import oauth2_scheme

listings_router = APIRouter(prefix="/listings")


@listings_router.post("/", response_model=Listing, dependencies=[Depends(oauth2_scheme)])
async def create_listing(
    create: CreateListingRequest,
    listings_logic: ListingsLogicDep,
    vehicles_logic: VehiclesLogicDep,
    plates_logic: PlatesLogicDep
):
    item: Union[Optional[Vehicle], Optional[Plate]] = None
    if create.listing_category is ListingCategory.Vehicle:
        item = await vehicles_logic.create(create.item)
    elif create.listing_category is ListingCategory.Plate:
        item = await plates_logic.create(create.item)

    listing = map_listing_response_to_listing(create)
    listing.item = item
    res = await listings_logic.create_listing(listing)
    res.item = item
    return res


@listings_router.get("/", response_model=ListingsResponse)
async def get_listings(listings_logic: ListingsLogicDep,
                       page: int = Query(1, ge=1, description="Page number"),
                       per_page: int = Query(
                           20, ge=1, le=50, description="Number of items per page"),
                        q: Optional[str] = Query(None, description="Search query in JSON format")):
    search = ListingSearchParams.from_query_string(q)
    res = await listings_logic.get_listings(page, per_page, search)
    return res


@listings_router.get("/{id}", response_model=Listing)
async def get_listing(listings_logic: ListingsLogicDep, id: str):
    res = await listings_logic.get_by_id(id)
    return res
