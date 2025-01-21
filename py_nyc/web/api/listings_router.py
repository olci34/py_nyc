from typing import Optional, Union
from fastapi import APIRouter, Request
from py_nyc.web.core.listings_logic import ListingsLogic
from py_nyc.web.core.plates_logic import PlatesLogic
from py_nyc.web.core.vehicles_logic import VehiclesLogic
from py_nyc.web.data_access.models.listing import Listing, ListingCategory, ListingResponse, Plate, Vehicle
from py_nyc.web.utils.listing_mapper import map_listing_response_to_listing


listings_router = APIRouter(prefix="/listings")


@listings_router.post("/", response_model=ListingResponse)
async def create_listing(listing_resp: ListingResponse, req: Request):
    listings_logic: ListingsLogic = req.app.state.listings_logic
    vehicles_logic: VehiclesLogic = req.app.state.vehicles_logic
    plates_logic: PlatesLogic = req.app.state.plates_logic
    item: Union[Optional[Vehicle], Optional[Plate]] = None
    print("REQ RECEIVED")
    if listing_resp.listing_category is ListingCategory.Vehicle:
        item = await vehicles_logic.create(listing_resp.item)
    elif listing_resp.listing_category is ListingCategory.Plate:
        item = await plates_logic.create(listing_resp.item)

    listing = map_listing_response_to_listing(listing_resp)
    listing.item = item
    res = await listings_logic.create_listing(listing)
    print(res.item)
    res.item = item
    return res
