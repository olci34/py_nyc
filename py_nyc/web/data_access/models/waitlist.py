from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field


class Waitlist(Document):
    email: EmailStr = Indexed(unique=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "waitlist"


class WaitlistResponse(BaseModel):
    email: EmailStr
    created_at: datetime
    updated_at: datetime
