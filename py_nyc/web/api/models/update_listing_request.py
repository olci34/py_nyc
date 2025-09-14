from datetime import datetime, timezone
from typing import List, Union, Optional
from pydantic import BaseModel, Field

from py_nyc.web.data_access.models.listing import Contact, Image, ListingCategory, ListingTransactionType, Location, Plate, Vehicle, ImageResponse


class UpdateListingRequest(BaseModel):
    title: str = Field(max_length=255, min_length=3)
    description: str = Field(max_length=2000, min_length=3)
    transaction_type: ListingTransactionType
    listing_category: ListingCategory
    item: Union[Vehicle, Plate] | None
    price: float = Field(gt=0)
    images: List[Image] = []
    location: Location
    contact: Optional[Contact] = None
    active: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
