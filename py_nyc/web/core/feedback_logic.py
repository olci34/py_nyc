from typing import Optional
from py_nyc.web.data_access.models.feedback import Feedback
from py_nyc.web.data_access.services.feedback_service import FeedbackService
from beanie import PydanticObjectId


class FeedbackLogic:
    def __init__(self, feedback_service: FeedbackService):
        self.feedback_service = feedback_service

    async def submit_feedback(self, text: str, visitor_id: str, user_id: Optional[PydanticObjectId] = None) -> Feedback:
        """Submit new feedback."""
        return await self.feedback_service.create(text, visitor_id, user_id)

    async def get_all_entries(self, offset: int = 0, limit: int = 100) -> list[Feedback]:
        """Get all feedback entries with pagination."""
        return await self.feedback_service.get_all(offset, limit)

    async def get_total_count(self) -> int:
        """Get total count of feedback entries."""
        return await self.feedback_service.get_count()

    async def get_by_user(self, user_id: PydanticObjectId) -> list[Feedback]:
        """Get feedback by user_id."""
        return await self.feedback_service.get_by_user_id(user_id)

    async def get_by_visitor(self, visitor_id: str) -> list[Feedback]:
        """Get feedback by visitor_id."""
        return await self.feedback_service.get_by_visitor_id(visitor_id)
