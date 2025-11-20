from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Payment status enum"""
    Pending = 'pending'
    Paid = 'paid'
    Failed = 'failed'
    Refunded = 'refunded'
    Cancelled = 'cancelled'


class PaymentType(str, Enum):
    """Type of payment"""
    Listing = 'listing'
    PromoteListing = 'promote_listing'
    # Future payment types can be added here


class PaymentMethodType(str, Enum):
    """Payment method type"""
    Card = 'card'
    ApplePay = 'apple_pay'
    GooglePay = 'google_pay'


class Payment(Document):
    """Payment document model for storing payment transactions"""
    user_id: PydanticObjectId = Indexed()
    stripe_payment_intent_id: str = Indexed(unique=True)  # Unique Stripe transaction ID
    stripe_session_id: Optional[str] = None  # Stripe checkout session ID

    amount: float = Field(gt=0)  # Amount in dollars
    currency: str = Field(default='usd')  # Currency code

    status: PaymentStatus = Field(default=PaymentStatus.Pending)
    payment_type: PaymentType  # Type of payment (listing, promote_listing, etc.)

    # Card/Payment method details
    last_4_digits: Optional[str] = None  # Last 4 digits of card
    card_brand: Optional[str] = None  # Visa, Mastercard, Amex, etc.
    payment_method_type: Optional[PaymentMethodType] = None  # card, apple_pay, google_pay

    # Related entities
    listing_id: Optional[PydanticObjectId] = None  # Associated listing ID

    # Subscription/Billing period (for monthly recurring)
    subscription_id: Optional[str] = None  # Stripe subscription ID if applicable
    period_start: Optional[datetime] = None  # Billing period start
    period_end: Optional[datetime] = None  # Billing period end

    # Metadata
    stripe_customer_id: Optional[str] = None  # Stripe customer ID
    error_message: Optional[str] = None  # Error message if payment failed

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "payments"


class PaymentResponse(BaseModel):
    """Response model for payment operations"""
    success: bool
    message: str
    payment_id: Optional[str] = None
    session_id: Optional[str] = None
    checkout_url: Optional[str] = None  # URL to redirect to Stripe-hosted checkout
    requires_payment: Optional[bool] = None


class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session"""
    payment_type: PaymentType
    listing_id: str  # Required - the inactive listing to be activated on payment success
    success_url: str
    cancel_url: str


class CheckPaymentRequirementResponse(BaseModel):
    """Response for checking if payment is required"""
    requires_payment: bool
    active_listings_count: int
    free_listings_remaining: int
    message: str


class SubscriptionInfoResponse(BaseModel):
    """Response for subscription/billing information"""
    active_listings_count: int
    monthly_charge: float
    price_per_listing: float
    currency: str
    free_listings_limit: int
    paid_listings_count: int
