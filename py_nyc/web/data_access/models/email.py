from typing import Optional, List
from datetime import datetime, timezone
from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class EmailType(str, Enum):
    """Types of emails sent by the system"""
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    WAITLIST_CONFIRMATION = "waitlist_confirmation"
    STRIPE_INVOICE = "stripe_invoice"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"


class EmailStatus(str, Enum):
    """Status of email delivery"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class Email(Document):
    """
    Email model to track all emails sent by the system.
    Stores metadata about sent emails for audit and debugging purposes.
    """
    # Recipient information
    to: EmailStr
    to_name: Optional[str] = None

    # Email content metadata
    subject: str
    email_type: EmailType

    # Sender information (usually from config)
    from_email: str
    from_name: str

    # Email service metadata
    provider: str = "resend"  # Email service provider
    provider_message_id: Optional[str] = None  # ID from email provider (e.g., Resend message ID)

    # Status tracking
    status: EmailStatus = EmailStatus.PENDING
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Related entities
    user_id: Optional[str] = None  # User who received the email
    stripe_invoice_id: Optional[str] = None  # For Stripe invoice emails
    stripe_subscription_id: Optional[str] = None  # For subscription-related emails
    listing_id: Optional[str] = None  # For listing-related emails

    # Template and variables (for future reference)
    template_data: Optional[dict] = None  # Variables used in the template

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "emails"
        indexes = [
            "to",
            "email_type",
            "status",
            "user_id",
            "stripe_invoice_id",
            "created_at"
        ]


class SendEmailRequest(BaseModel):
    """Request model for sending an email"""
    to: EmailStr
    to_name: Optional[str] = None
    subject: str
    html: str
    email_type: EmailType
    user_id: Optional[str] = None
    template_data: Optional[dict] = None


class SendEmailResponse(BaseModel):
    """Response model after sending an email"""
    success: bool
    message: str
    email_id: Optional[str] = None  # Database ID
    provider_message_id: Optional[str] = None  # Resend message ID
