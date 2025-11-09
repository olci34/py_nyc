from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel, EmailStr
from py_nyc.web.data_access.models.waitlist import WaitlistResponse
from py_nyc.web.dependencies import WaitlistLogicDep


class JoinWaitlistRequest(BaseModel):
    email: EmailStr


waitlist_router = APIRouter(prefix='/waitlist')


@waitlist_router.post('/join', response_model=WaitlistResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(waitlist_logic: WaitlistLogicDep, request: JoinWaitlistRequest = Body()):
    """
    Add an email to the waitlist.
    If the email already exists, updates the updated_at timestamp.
    """
    try:
        waitlist_entry = await waitlist_logic.join_waitlist(request.email)
        return WaitlistResponse(
            email=waitlist_entry.email,
            created_at=waitlist_entry.created_at,
            updated_at=waitlist_entry.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join waitlist: {str(e)}"
        )


@waitlist_router.get('/entries', response_model=list[WaitlistResponse])
async def get_waitlist_entries(waitlist_logic: WaitlistLogicDep, offset: int = 0, limit: int = 100):
    """
    Get all waitlist entries with pagination.
    This endpoint might be protected with authentication in production.
    """
    entries = await waitlist_logic.get_all_entries(offset, limit)
    return [
        WaitlistResponse(
            email=entry.email,
            created_at=entry.created_at,
            updated_at=entry.updated_at
        )
        for entry in entries
    ]


@waitlist_router.get('/count')
async def get_waitlist_count(waitlist_logic: WaitlistLogicDep):
    """
    Get total count of waitlist entries.
    This endpoint might be protected with authentication in production.
    """
    count = await waitlist_logic.get_total_count()
    return {"count": count}
