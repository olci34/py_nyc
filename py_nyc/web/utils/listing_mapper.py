import base64
from beanie import BsonBinary
from py_nyc.web.data_access.models.listing import Image, ImageResponse, Listing, ListingResponse


def map_listing_to_listing_response(listing: Listing) -> ListingResponse:
    mapped_images = [map_image_to_image_response(
        img) for img in listing.images]
    res = ListingResponse(images=mapped_images, **
                          listing.model_dump(exclude={"images"}))

    return res


def map_listing_response_to_listing(listing_response: ListingResponse) -> Listing:
    imgs = [map_image_response_to_image(img)
            for img in listing_response.images]
    res = Listing(
        images=imgs, item=None, **listing_response.model_dump(exclude={"images", "item"}))

    return res


def map_image_response_to_image(image_response: ImageResponse) -> Image:
    # binary_data = BsonBinary(base64.b64decode(image_response.image_data))
    return Image(**image_response.model_dump())


def map_image_to_image_response(image: Image) -> ImageResponse:
    # image_base64 = base64.b64encode(image.image_data).decode("utf-8")
    return ImageResponse(
        name=image.name,
        src=image.src,
        cld_public_id=image.cld_public_id,
        file_type=image.file_type,
        file_size=image.file_size
    )
