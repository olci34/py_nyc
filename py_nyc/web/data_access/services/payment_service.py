from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.data_access.models.payment import Payment, PaymentStatus
from beanie import PydanticObjectId
from datetime import datetime, timezone


class PaymentService:
    """Service layer for payment database operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.payments_collection = db.get_collection('payments')

    async def create(self, payment: Payment) -> Payment:
        """Create a new payment record"""
        return await payment.create()

    async def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        return await Payment.get(payment_id)

    async def get_by_payment_intent_id(self, payment_intent_id: str) -> Optional[Payment]:
        """Get payment by Stripe payment intent ID"""
        return await Payment.find_one(Payment.stripe_payment_intent_id == payment_intent_id)

    async def get_by_session_id(self, session_id: str) -> Optional[Payment]:
        """Get payment by Stripe session ID"""
        return await Payment.find_one(Payment.stripe_session_id == session_id)

    async def get_user_payments(
        self,
        user_id: PydanticObjectId,
        offset: int = 0,
        limit: int = 20
    ) -> List[Payment]:
        """Get all payments for a user"""
        return await Payment.find(
            Payment.user_id == user_id
        ).skip(offset).limit(limit).sort(-Payment.created_at).to_list()

    async def update_payment_status(
        self,
        payment_id: str,
        status: PaymentStatus,
        error_message: Optional[str] = None
    ) -> Optional[Payment]:
        """Update payment status"""
        payment = await self.get_by_id(payment_id)
        if payment:
            payment.status = status
            payment.updated_at = datetime.now(timezone.utc)
            if error_message:
                payment.error_message = error_message
            await payment.save()
        return payment

    async def update_payment_details(
        self,
        payment_intent_id: str,
        status: PaymentStatus,
        last_4_digits: Optional[str] = None,
        card_brand: Optional[str] = None,
        payment_method_type: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Payment]:
        """Update payment details after Stripe webhook"""
        payment = await self.get_by_payment_intent_id(payment_intent_id)
        if payment:
            payment.status = status
            if last_4_digits:
                payment.last_4_digits = last_4_digits
            if card_brand:
                payment.card_brand = card_brand
            if payment_method_type:
                payment.payment_method_type = payment_method_type
            if stripe_customer_id:
                payment.stripe_customer_id = stripe_customer_id
            if error_message:
                payment.error_message = error_message
            payment.updated_at = datetime.now(timezone.utc)
            await payment.save()
        return payment

    async def count_active_user_listings_with_payments(self, user_id: PydanticObjectId) -> int:
        """
        Count how many active listings the user has that required payment.
        This helps determine if a new listing needs payment.
        """
        # This will be implemented in conjunction with listing logic
        # For now, we'll count successful payments of type 'listing'
        count = await Payment.find(
            Payment.user_id == user_id,
            Payment.payment_type == "listing",
            Payment.status == PaymentStatus.Paid
        ).count()
        return count
