from typing import Optional
from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field


class User(Document):
  email: EmailStr = Indexed(unique=True)
  password: str
  first_name: str
  last_name: str
  visitor_id: Optional[str] = None
  created_at: datetime = Field(
      default_factory=lambda: datetime.now(timezone.utc))
  updated_at: datetime = Field(
      default_factory=lambda: datetime.now(timezone.utc))

  class Settings:
    name = "users"


class UserResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    visitor_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime