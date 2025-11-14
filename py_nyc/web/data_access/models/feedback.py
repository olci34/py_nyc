from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import BaseModel, Field
from beanie import PydanticObjectId


class Feedback(Document):
    text: str
    user_id: Optional[PydanticObjectId] = None
    visitor_id: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "feedback"


class FeedbackResponse(BaseModel):
    text: str
    user_id: Optional[str] = None
    visitor_id: str
    created_at: datetime
    updated_at: datetime
