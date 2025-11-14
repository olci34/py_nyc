from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.data_access.models.feedback import Feedback
from beanie import PydanticObjectId


class FeedbackService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.feedback_collection = db.get_collection('feedback')

    async def create(self, text: str, visitor_id: str, user_id: Optional[PydanticObjectId] = None) -> Feedback:
        """
        Create a new feedback entry.
        """
        feedback_entry = Feedback(
            text=text,
            visitor_id=visitor_id,
            user_id=user_id
        )
        await feedback_entry.create()
        return feedback_entry

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Feedback]:
        """Get all feedback entries with pagination."""
        return await Feedback.find_all().skip(offset).limit(limit).to_list()

    async def get_count(self) -> int:
        """Get total count of feedback entries."""
        return await Feedback.find_all().count()

    async def get_by_user_id(self, user_id: PydanticObjectId) -> list[Feedback]:
        """Get all feedback entries by user_id."""
        return await Feedback.find(Feedback.user_id == user_id).to_list()

    async def get_by_visitor_id(self, visitor_id: str) -> list[Feedback]:
        """Get all feedback entries by visitor_id."""
        return await Feedback.find(Feedback.visitor_id == visitor_id).to_list()
