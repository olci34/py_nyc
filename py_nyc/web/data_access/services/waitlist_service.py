from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.data_access.models.waitlist import Waitlist


class WaitlistService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.waitlist_collection = db.get_collection('waitlist')

    async def get_by_email(self, email: str) -> Waitlist | None:
        """Check if an email already exists in the waitlist."""
        return await Waitlist.find_one(Waitlist.email == email)

    async def create(self, email: str) -> Waitlist:
        """Create a new waitlist entry."""
        waitlist_entry = Waitlist(email=email)
        await waitlist_entry.create()
        return waitlist_entry

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Waitlist]:
        """Get all waitlist entries with pagination."""
        return await Waitlist.find_all().skip(offset).limit(limit).to_list()

    async def get_count(self) -> int:
        """Get total count of waitlist entries."""
        return await Waitlist.find_all().count()
