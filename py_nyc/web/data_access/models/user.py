from typing import Optional
from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field
from pymongo import IndexModel, ASCENDING


class User(Document):
    email: EmailStr = Indexed(unique=True)
    password: Optional[str] = None
    first_name: str
    last_name: str
    google_id: Optional[str] = None
    visitor_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None  # Stripe Customer ID for billing
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            # Index for fast google_id lookups (not unique, sparse to ignore nulls)
            IndexModel([("google_id", ASCENDING)], sparse=True)
        ]


class UserResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    visitor_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
