from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Union
from beanie import Document, Indexed, Link
from pydantic import BaseModel, Field


class ListingCategory(str, Enum):
    Vehicle = 'Vehicle'
    Plate = 'Plate'


class ListingTransactionType(str, Enum):
    Rental = 'Rental'
    Sale = 'Sale'


class FuelType(str, Enum):
    Gas = 'Gas',
    Diesel = 'Diesel',
    Hybrid = 'Hybrid',
    Electric = 'Electric'


class Vehicle(Document):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[float] = None
    fuel: Optional[FuelType] = None
    color: Optional[str] = None
    details: Optional[str] = None

    class Settings:
        name = "vehicles"


class Plate(Document):
    plate_number: Optional[str] = None
    base_number: Optional[str] = None

    class Settings:
        name = "plates"


class Contact(BaseModel):
    phone: str
    email: str


class Location(BaseModel):
    county: Optional[str]
    city: str
    state: str


class Image(BaseModel):
    name: str
    src: str
    cld_public_id: str
    file_type: str
    file_size: float


class ImageResponse(BaseModel):
    name: str
    src: str
    cld_public_id: str
    file_type: str
    file_size: float


class ListingResponse(BaseModel):
    title: str = Field(max_length=255, min_length=3)
    description: str = Field(max_length=2000, min_length=3)
    transaction_type: ListingTransactionType
    listing_category: ListingCategory
    item: Union[Vehicle, Plate] | None
    # listing_code: int = Indexed(int, unique=True)
    price: float = Field(gt=0)
    location: Location
    contact: Optional[Contact] = None
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
    # listing_code: int = Indexed(int, unique=True)
    price: float = Field(gt=0)
    location: Location
    contact: Optional[Contact] = None
    active: bool = True
    images: List[Image] = []
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    class Settings:
        name = "listings"


class ListingsResponse(BaseModel):
    listings: List[Listing]
    total: int
