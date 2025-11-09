from py_nyc.web.data_access.models.waitlist import Waitlist
from py_nyc.web.data_access.services.waitlist_service import WaitlistService


class WaitlistLogic:
    def __init__(self, waitlist_service: WaitlistService):
        self.waitlist_service = waitlist_service

    async def join_waitlist(self, email: str) -> Waitlist:
        """Add or update an email in the waitlist."""
        return await self.waitlist_service.upsert(email)

    async def get_all_entries(self, offset: int = 0, limit: int = 100) -> list[Waitlist]:
        """Get all waitlist entries with pagination."""
        return await self.waitlist_service.get_all(offset, limit)

    async def get_total_count(self) -> int:
        """Get total count of waitlist entries."""
        return await self.waitlist_service.get_count()
