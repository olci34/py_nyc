from typing import Optional, Union
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from py_nyc.web.dependencies import ListingsLogicDep, PlatesLogicDep, VehiclesLogicDep
from .schemas import ListingSearchParams
from ..data_access.models.listing import Image, Listing, ListingCategory, ListingsResponse, Plate, Vehicle, ImageResponse
from py_nyc.web.utils.listing_mapper import map_listing_request_to_listing, map_image_response_to_image
from py_nyc.web.utils.auth import get_user_info
from beanie import PydanticObjectId
from datetime import datetime, timezone
from .cloudinary_router import DeleteImagesRequest, delete_images, upload_images
from .models.update_listing_request import UpdateListingRequest
import json
import logging

logger = logging.getLogger(__name__)

listings_router = APIRouter(prefix="/listings")


def parse_listing_form_data(listing_json: str) -> UpdateListingRequest:
    """Parse listing JSON data from FormData into CreateListingRequest object"""
    try:
        listing_data = json.loads(listing_json)
        return UpdateListingRequest(**listing_data)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format in listing data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid listing data: {str(e)}"
        )


async def process_image_files(uploaded_files) -> list[Image]:
    """Process uploaded image files and combine with existing images"""
    if not uploaded_files:
        return []

    # Upload new files to Cloudinary
    cloudinary_response = await upload_images(uploaded_files)
    new_images = [
        Image(
            name=img["name"],
            src=img["src"],
            cld_public_id=img["cld_public_id"],
            file_size=img["file_size"],
            file_type=img["file_type"]
        ) for img in cloudinary_response["images"]
    ]

    return new_images


@listings_router.post("/", response_model=Listing)
async def create_listing(
    request: Request,
    listings_logic: ListingsLogicDep,
    vehicles_logic: VehiclesLogicDep,
    plates_logic: PlatesLogicDep,
    user=Depends(get_user_info)
):
    form = await request.form()
    listing_json = form.get('listing')

    if not listing_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing listing data in FormData. Available keys: {list(form.keys())}"
        )

    listing = parse_listing_form_data(listing_json)

    uploaded_files = form.getlist('images')

    item: Union[Optional[Vehicle], Optional[Plate]] = None
    if listing.listing_category is ListingCategory.Vehicle:
        item = await vehicles_logic.create(listing.item)
    elif listing.listing_category is ListingCategory.Plate:
        item = await plates_logic.create(listing.item)

    uploaded_images = await process_image_files(uploaded_files)

    new_listing = map_listing_request_to_listing(
        listing, PydanticObjectId(user.id))
    new_listing.item = item
    new_listing.images = uploaded_images

    res = await listings_logic.create_listing(new_listing)

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


@listings_router.delete("/photos/{id}", response_model=bool)
async def delete_photo(listings_logic: ListingsLogicDep, id: str):
    return await listings_logic.delete_photo(id)


@listings_router.get("/user/{user_id}", response_model=ListingsResponse)
async def get_user_listings(
    user_id: str,
    listings_logic: ListingsLogicDep,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(
        20, ge=1, le=50, description="Number of items per page"),
    user=Depends(get_user_info)
):
    if user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to access listings for this user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await listings_logic.get_user_listings(PydanticObjectId(user_id), page, per_page)


@listings_router.put("/{id}", response_model=Listing)
async def edit_listing(
    id: str,
    request: Request,
    listings_logic: ListingsLogicDep,
    vehicles_logic: VehiclesLogicDep,
    plates_logic: PlatesLogicDep,
    user=Depends(get_user_info)
):
    form = await request.form()
    listing_json = form.get('listing')

    if not listing_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing listing data in FormData"
        )

    update = parse_listing_form_data(listing_json)

    current_listing = await listings_logic.get_by_id(id)
    if current_listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if str(current_listing.user_id) != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to edit this listing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Remove images
    image_diff = [
        img for img in current_listing.images if img not in update.images]
    if len(image_diff) > 0:
        cld_public_ids = [img.cld_public_id for img in image_diff]
        del_img_req = DeleteImagesRequest(public_ids=cld_public_ids)
        await delete_images(del_img_req)

    current_listing.images = update.images

    # Add new images
    new_images = form.getlist('images')
    if new_images:
        add_images = await process_image_files(new_images)
        current_listing.images.extend(add_images)

    if update.item is not None:
        await current_listing.fetch_link("item")

        data = update.item.model_dump(
            exclude_unset=True, exclude={"id", "_id"})
        if current_listing.item:
            for k, v in data.items():
                setattr(current_listing.item, k, v)
            await current_listing.item.save()
        else:
            new_item = await (vehicles_logic.create(update.item) if update.listing_category is ListingCategory.Vehicle else plates_logic.create(update.item))
            current_listing.item = new_item

    # Update listing fields
    current_listing.title = update.title
    current_listing.description = update.description
    current_listing.transaction_type = update.transaction_type
    current_listing.listing_category = update.listing_category
    current_listing.price = update.price
    current_listing.location = update.location
    current_listing.contact = update.contact
    current_listing.active = update.active
    current_listing.updated_at = datetime.now(timezone.utc)

    updated = await listings_logic.update_listing(current_listing)
    return updated


@listings_router.delete("/{id}", response_model=Listing)
async def delete_listing(
    id: str,
    listings_logic: ListingsLogicDep,
    user=Depends(get_user_info)
):
    """
    Soft delete a listing by setting active to False and delete all images from Cloudinary
    """
    current_listing = await listings_logic.get_by_id(id)

    if current_listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    if str(current_listing.user_id) != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to delete this listing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Delete all images from Cloudinary
    if current_listing.images and len(current_listing.images) > 0:
        cld_public_ids = [img.cld_public_id for img in current_listing.images]
        del_img_req = DeleteImagesRequest(public_ids=cld_public_ids)
        await delete_images(del_img_req)

    # Soft delete the listing
    deleted_listing = await listings_logic.soft_delete_listing(id)
    return deleted_listing
