from fastapi import APIRouter, Body, HTTPException, status, Depends, Request, Header
from typing import Optional
import stripe
from py_nyc.web.dependencies import PaymentsLogicDep
from py_nyc.web.data_access.models.payment import (
    CreateCheckoutSessionRequest,
    PaymentResponse,
    CheckPaymentRequirementResponse,
    SubscriptionInfoResponse,
    PaymentType
)
from py_nyc.web.utils.auth import get_user_info
from py_nyc.web.core.config import Settings, get_settings
from beanie import PydanticObjectId
import logging

logger = logging.getLogger(__name__)

payments_router = APIRouter(prefix="/payments")


@payments_router.get("/check-requirement", response_model=CheckPaymentRequirementResponse)
async def check_payment_requirement(
    payments_logic: PaymentsLogicDep,
    user=Depends(get_user_info)
):
    """
    Check if the user needs to pay to create a new listing.
    First 2 active listings are free.
    """
    try:
        return await payments_logic.check_payment_requirement(
            PydanticObjectId(user.id)
        )
    except Exception as e:
        logger.error(f"Error checking payment requirement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check payment requirement"
        )


@payments_router.post("/create-checkout-session", response_model=PaymentResponse)
async def create_checkout_session(
    payments_logic: PaymentsLogicDep,
    request: CreateCheckoutSessionRequest = Body(),
    user=Depends(get_user_info)
):
    """
    Create a Stripe Checkout session for payment.
    This session supports Apple Pay, Google Pay, and manual card entry.
    """
    try:
        return await payments_logic.create_checkout_session(
            user_id=PydanticObjectId(user.id),
            user_email=user.email,
            payment_type=request.payment_type,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            listing_id=request.listing_id
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@payments_router.post("/webhook")
async def stripe_webhook(
    request: Request,
    payments_logic: PaymentsLogicDep,
    settings: Settings = Depends(get_settings),
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Stripe webhook endpoint to handle payment events.
    This endpoint is called by Stripe when payment events occur.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    # Get raw body
    payload = await request.body()

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    # Handle the event
    event_type = event['type']
    event_data = event['data']['object']

    logger.info(f"Received Stripe webhook event: {event_type}")

    try:
        result = await payments_logic.handle_webhook_event(event_type, event_data)

        if not result.success:
            logger.error(f"Webhook handler returned error: {result.message}")

        return {"status": "success", "message": result.message}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@payments_router.get("/history")
async def get_payment_history(
    payments_logic: PaymentsLogicDep,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_user_info)
):
    """
    Get user's payment history.
    """
    try:
        payments = await payments_logic.get_user_payments(
            PydanticObjectId(user.id),
            page,
            per_page
        )
        return {
            "payments": payments,
            "total": len(payments)
        }
    except Exception as e:
        logger.error(f"Error fetching payment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment history"
        )


@payments_router.get("/config")
async def get_stripe_config(
    payments_logic: PaymentsLogicDep,
    settings: Settings = Depends(get_settings)
):
    """
    Get Stripe publishable key and pricing information for frontend.
    This is safe to expose publicly.
    """
    price_info = payments_logic.get_listing_price_info()

    return {
        "publishable_key": settings.stripe_publishable_key,
        "price_per_listing": price_info["amount"],
        "currency": price_info["currency"],
        "recurring_interval": price_info["recurring"]
    }


@payments_router.get("/subscription-info", response_model=SubscriptionInfoResponse)
async def get_subscription_info(
    payments_logic: PaymentsLogicDep,
    user=Depends(get_user_info)
):
    """
    Get user's subscription and billing information.
    Returns active listings count and calculated monthly charge.
    """
    try:
        return await payments_logic.get_subscription_info(
            PydanticObjectId(user.id)
        )
    except Exception as e:
        logger.error(f"Error fetching subscription info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription information"
        )
