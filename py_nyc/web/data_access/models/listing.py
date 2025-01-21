from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Union
from beanie import BsonBinary, Document, Indexed, Link
from pydantic import BaseModel, Field


class Vehicle(Document):
    make: str
    model: str
    year: int
    mileage: float
    color: Optional[str]
    details: Optional[str]

    class Settings:
        name = "vehicles"


class Plate(Document):
    plate_number: str
    base_number: Optional[str]

    class Settings:
        name = "plates"


class ListingCategory(str, Enum):
    Vehicle = 'Vehicle'
    Plate = 'Plate'


class ListingTransactionType(str, Enum):
    Rental = 'Rental'
    Sale = 'Sale'


class Location(BaseModel):
    county: Optional[str]
    city: str
    state: str


class Image(BaseModel):
    name: str
    file_type: str
    file_size: float  # kilobytes
    image_data: BsonBinary


class ImageResponse(BaseModel):
    name: str
    file_type: str
    file_size: float  # kilobytes
    image_data: str


class ListingResponse(BaseModel):
    title: str = Field(max_length=255, min_length=3)
    description: str = Field(max_length=1000, min_length=3)
    transaction_type: ListingTransactionType
    listing_category: ListingCategory
    item: Union[Vehicle, Plate] | None
    listing_code: int = Indexed(int, unique=True)
    price: float = Field(gt=0)
    location: Location
    active: bool = True
    images: List[ImageResponse] = []
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class Listing(Document):
    title: str = Field(max_length=255, min_length=3)
    description: str = Field(max_length=1000, min_length=3)
    transaction_type: ListingTransactionType
    listing_category: ListingCategory
    item: Link[Vehicle] | Link[Plate] | None
    listing_code: int = Indexed(int, unique=True)
    price: float = Field(gt=0)
    location: Location
    active: bool = True
    images: List[Image] = []
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    class Settings:
        name = "listings"
