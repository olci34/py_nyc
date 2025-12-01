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

    # Legal consent tracking (for audit/compliance proof)
    legal_consent_accepted: bool = False
    legal_consent_accepted_at: Optional[datetime] = None
    legal_consent_ip_address: Optional[str] = None  # IP address when consent was given
    legal_consent_user_agent: Optional[str] = None  # Browser/device info when consent was given
    legal_consent_version: str = "1.0"  # Version of Terms/Privacy at time of consent

    # Cookie consent tracking (for U.S. compliance)
    cookie_consent_accepted: Optional[bool] = None
    cookie_consent_accepted_at: Optional[datetime] = None
    cookie_consent_ip_address: Optional[str] = None  # IP address when cookie consent was given
    cookie_consent_user_agent: Optional[str] = None  # Browser/device info when cookie consent was given

    # Account deletion tracking (soft delete with 7-day grace period)
    scheduled_for_deletion_at: Optional[datetime] = None  # When user requested deletion

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
