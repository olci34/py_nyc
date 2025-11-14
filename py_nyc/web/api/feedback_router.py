from typing import Optional
from fastapi import APIRouter, Body, HTTPException, status, Depends
from pydantic import BaseModel
from py_nyc.web.data_access.models.feedback import FeedbackResponse
from py_nyc.web.dependencies import FeedbackLogicDep
from py_nyc.web.utils.auth import get_user_info_optional
from beanie import PydanticObjectId


class SubmitFeedbackRequest(BaseModel):
    text: str
    visitor_id: str


feedback_router = APIRouter(prefix='/feedback')


@feedback_router.post('/submit', response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_logic: FeedbackLogicDep,
    request: SubmitFeedbackRequest = Body(),
    user=Depends(get_user_info_optional)
):
    """
    Submit feedback.
    Captures user_id if authenticated, otherwise just visitor_id.
    """
    try:
        user_id = PydanticObjectId(user.id) if user else None

        feedback_entry = await feedback_logic.submit_feedback(
            text=request.text,
            visitor_id=request.visitor_id,
            user_id=user_id
        )

        return FeedbackResponse(
            text=feedback_entry.text,
            user_id=str(feedback_entry.user_id) if feedback_entry.user_id else None,
            visitor_id=feedback_entry.visitor_id,
            created_at=feedback_entry.created_at,
            updated_at=feedback_entry.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@feedback_router.get('/entries', response_model=list[FeedbackResponse])
async def get_feedback_entries(feedback_logic: FeedbackLogicDep, offset: int = 0, limit: int = 100):
    """
    Get all feedback entries with pagination.
    This endpoint might be protected with authentication in production.
    """
    entries = await feedback_logic.get_all_entries(offset, limit)
    return [
        FeedbackResponse(
            text=entry.text,
            user_id=str(entry.user_id) if entry.user_id else None,
            visitor_id=entry.visitor_id,
            created_at=entry.created_at,
            updated_at=entry.updated_at
        )
        for entry in entries
    ]


@feedback_router.get('/count')
async def get_feedback_count(feedback_logic: FeedbackLogicDep):
    """
    Get total count of feedback entries.
    This endpoint might be protected with authentication in production.
    """
    count = await feedback_logic.get_total_count()
    return {"count": count}
