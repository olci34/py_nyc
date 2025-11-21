from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.data_access.models.email import Email, EmailStatus, EmailType
from datetime import datetime, timezone
from typing import Optional, List


class EmailService:
    """
    Data access service for Email model.
    Handles all database operations related to emails.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.emails_collection = db.get_collection('emails')

    async def create(self, email: Email) -> Email:
        """Create a new email record"""
        return await email.create()

    async def get_by_id(self, email_id: str) -> Optional[Email]:
        """Get email by ID"""
        return await Email.get(email_id)

    async def update_status(
        self,
        email_id: str,
        status: EmailStatus,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Email]:
        """Update email status and related fields"""
        email = await Email.get(email_id)
        if not email:
            return None

        email.status = status
        email.updated_at = datetime.now(timezone.utc)

        if provider_message_id:
            email.provider_message_id = provider_message_id

        if status == EmailStatus.SENT:
            email.sent_at = datetime.now(timezone.utc)
        elif status == EmailStatus.DELIVERED:
            email.delivered_at = datetime.now(timezone.utc)
        elif status == EmailStatus.FAILED or status == EmailStatus.BOUNCED:
            email.failed_at = datetime.now(timezone.utc)
            if error_message:
                email.error_message = error_message

        await email.save()
        return email

    async def get_user_emails(
        self,
        user_id: str,
        email_type: Optional[EmailType] = None,
        limit: int = 50
    ) -> List[Email]:
        """Get emails sent to a specific user"""
        query = {"user_id": user_id}
        if email_type:
            query["email_type"] = email_type

        emails = await Email.find(query).sort("-created_at").limit(limit).to_list()
        return emails

    async def get_by_stripe_invoice(self, stripe_invoice_id: str) -> Optional[Email]:
        """Get email by Stripe invoice ID"""
        return await Email.find_one(Email.stripe_invoice_id == stripe_invoice_id)

    async def get_recent_emails(
        self,
        limit: int = 100,
        status: Optional[EmailStatus] = None
    ) -> List[Email]:
        """Get recent emails, optionally filtered by status"""
        query = {}
        if status:
            query["status"] = status

        emails = await Email.find(query).sort("-created_at").limit(limit).to_list()
        return emails

    async def count_by_type(self, email_type: EmailType) -> int:
        """Count emails by type"""
        return await Email.find(Email.email_type == email_type).count()

    async def count_by_status(self, status: EmailStatus) -> int:
        """Count emails by status"""
        return await Email.find(Email.status == status).count()
