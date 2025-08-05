from datetime import datetime, timezone
from typing import List, Union
from pydantic import BaseModel, Field

from py_nyc.web.data_access.models.listing import ImageResponse, ListingCategory, ListingTransactionType, Location, Plate, Vehicle


class CreateListingRequest(BaseModel):
    title: str = Field(max_length=255, min_length=3)
    description: str = Field(max_length=2000, min_length=3)
    transaction_type: ListingTransactionType
    listing_category: ListingCategory
    item: Union[Vehicle, Plate] | None
    price: float = Field(gt=0)
    location: Location
    active: bool = True
    images: List[ImageResponse] = []
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
