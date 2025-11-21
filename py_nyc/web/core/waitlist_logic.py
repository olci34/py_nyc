from typing import Optional, TYPE_CHECKING
from py_nyc.web.data_access.models.waitlist import Waitlist
from py_nyc.web.data_access.services.waitlist_service import WaitlistService

if TYPE_CHECKING:
    from py_nyc.web.core.email_logic import EmailLogic


class WaitlistLogic:
    def __init__(
        self,
        waitlist_service: WaitlistService,
        email_logic: Optional["EmailLogic"] = None
    ):
        self.waitlist_service = waitlist_service
        self.email_logic = email_logic

    async def join_waitlist(self, email: str) -> Waitlist:
        """
        Add or update an email in the waitlist.
        Sends confirmation email if email_logic is available.
        """
        waitlist_entry = await self.waitlist_service.upsert(email)

        # Send confirmation email if email logic is available
        if self.email_logic:
            try:
                await self.email_logic.send_waitlist_confirmation_email(
                    to_email=email,
                    to_name=None  # Waitlist doesn't collect names
                )
            except Exception as e:
                # Log error but don't fail the waitlist join
                print(f"Failed to send waitlist confirmation email: {str(e)}")

        return waitlist_entry

    async def get_all_entries(self, offset: int = 0, limit: int = 100) -> list[Waitlist]:
        """Get all waitlist entries with pagination."""
        return await self.waitlist_service.get_all(offset, limit)

    async def get_total_count(self) -> int:
        """Get total count of waitlist entries."""
        return await self.waitlist_service.get_count()
