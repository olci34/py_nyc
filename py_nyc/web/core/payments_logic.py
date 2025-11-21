from typing import Optional, TYPE_CHECKING
import stripe
from beanie import PydanticObjectId
from py_nyc.web.data_access.models.payment import (
    Payment,
    PaymentStatus,
    PaymentType,
    PaymentMethodType,
    PaymentResponse,
    CheckPaymentRequirementResponse,
    SubscriptionInfoResponse
)
from py_nyc.web.data_access.services.payment_service import PaymentService
from py_nyc.web.data_access.services.listing_service import ListingService
from py_nyc.web.data_access.services.user_service import UserService
from py_nyc.web.core.config import Settings

if TYPE_CHECKING:
    from py_nyc.web.core.email_logic import EmailLogic


class PaymentsLogic:
    """Business logic for payment operations"""

    FREE_LISTINGS_LIMIT = 2  # First 2 active listings are free

    def __init__(
        self,
        payment_service: PaymentService,
        listing_service: ListingService,
        user_service: UserService,
        settings: Settings,
        email_logic: Optional["EmailLogic"] = None
    ):
        self.payment_service = payment_service
        self.listing_service = listing_service
        self.user_service = user_service
        self.settings = settings
        self.email_logic = email_logic
        # Initialize Stripe with secret key
        stripe.api_key = settings.stripe_secret_key

    async def get_or_create_stripe_customer(
        self,
        user_id: PydanticObjectId,
        user_email: str,
        user_name: str
    ) -> str:
        """
        Get existing Stripe Customer ID or create new customer.
        Stores customer_id in user record for future use.
        Returns: Stripe Customer ID
        """
        # Check if user already has a Stripe customer ID
        user = await self.user_service.get_by_id(str(user_id))

        if user and user.stripe_customer_id:
            # Verify customer exists in Stripe
            try:
                customer = stripe.Customer.retrieve(user.stripe_customer_id)
                if customer and not customer.get('deleted'):
                    return user.stripe_customer_id
            except stripe.error.StripeError:
                # Customer doesn't exist in Stripe, will create new one
                pass

        # Create new Stripe customer
        try:
            customer = stripe.Customer.create(
                email=user_email,
                name=user_name,
                metadata={
                    'user_id': str(user_id)
                }
            )

            # Store customer_id in user record
            await self.user_service.update_stripe_customer_id(
                str(user_id),
                customer.id
            )

            return customer.id
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create Stripe customer: {str(e)}")

    async def check_payment_requirement(
        self,
        user_id: PydanticObjectId
    ) -> CheckPaymentRequirementResponse:
        """
        Check if user needs to pay for creating a new listing.
        First 2 active listings are free.
        """
        # Count user's active listings
        active_listings_count = await self._count_user_active_listings(user_id)

        requires_payment = active_listings_count >= self.FREE_LISTINGS_LIMIT
        free_remaining = max(
            0, self.FREE_LISTINGS_LIMIT - active_listings_count)

        # Get current price from Stripe
        price_info = self.get_listing_price_info()
        price_display = f"${price_info['amount']:.2f}"
        interval = price_info['recurring'] or 'month'

        if requires_payment:
            message = (
                f"You have {active_listings_count} active listings. "
                f"Additional listings require a {price_display}/{interval} payment."
            )
        else:
            message = (
                f"You have {active_listings_count} active listing(s). "
                f"You can create {free_remaining} more free listing(s)."
            )

        return CheckPaymentRequirementResponse(
            requires_payment=requires_payment,
            active_listings_count=active_listings_count,
            free_listings_remaining=free_remaining,
            message=message
        )

    async def create_checkout_session(
        self,
        user_id: PydanticObjectId,
        user_email: str,
        payment_type: PaymentType,
        listing_id: str,
        success_url: str,
        cancel_url: str
    ) -> PaymentResponse:
        """
        Create a Stripe Checkout session for recurring subscription payment.
        Supports Apple Pay, Google Pay, and card payments.

        listing_id: Required - the inactive listing that will be activated on payment success
        Creates a monthly recurring subscription in Stripe.
        """
        try:
            # Get or create Stripe Customer
            user = await self.user_service.get_by_id(str(user_id))
            if not user:
                return PaymentResponse(
                    success=False,
                    message="User not found"
                )

            user_name = f"{user.first_name} {user.last_name}"
            stripe_customer_id = await self.get_or_create_stripe_customer(
                user_id,
                user_email,
                user_name
            )

            # Append listing_id to success and cancel URLs
            success_url_with_id = f"{success_url}?listing_id={listing_id}"
            cancel_url_with_id = f"{cancel_url}?listing_id={listing_id}"

            # Create Stripe checkout session using Price ID from Stripe Dashboard
            # Mode is 'subscription' for recurring monthly billing
            session = stripe.checkout.Session.create(
                # This includes Apple Pay and Google Pay automatically
                payment_method_types=['card'],
                mode='subscription',  # SUBSCRIPTION MODE for recurring billing
                customer=stripe_customer_id,  # Use customer ID instead of customer_email
                line_items=[{
                    'price': self.settings.stripe_listing_price_id,
                    'quantity': 1,
                }],
                success_url=success_url_with_id,
                cancel_url=cancel_url_with_id,
                metadata={
                    'user_id': str(user_id),
                    'payment_type': payment_type.value,
                    'listing_id': listing_id
                }
            )

            # Get price info from Stripe
            price_info = self.get_listing_price_info()

            # Create payment record in database (pending status)
            # Note: subscription_id will be updated via webhook when subscription is created
            payment = Payment(
                user_id=user_id,
                # subscription ID for subscription mode
                stripe_payment_intent_id=session.subscription or session.id,
                stripe_session_id=session.id,
                amount=price_info['amount'],
                currency=price_info['currency'],
                status=PaymentStatus.Pending,
                payment_type=payment_type,
                listing_id=PydanticObjectId(
                    listing_id) if listing_id else None,
                subscription_id=None,  # Will be set when checkout completes
                stripe_customer_id=stripe_customer_id  # Store customer ID
            )
            created_payment = await self.payment_service.create(payment)

            return PaymentResponse(
                success=True,
                message="Checkout session created successfully. Please complete your payment to activate your listing.",
                payment_id=str(created_payment.id),
                session_id=session.id,
                checkout_url=session.url  # URL to redirect user to Stripe-hosted checkout
            )

        except stripe.error.StripeError as e:
            return PaymentResponse(
                success=False,
                message=f"Payment processing error: {str(e)}"
            )
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"An unexpected error occurred: {str(e)}"
            )

    async def handle_webhook_event(self, event_type: str, event_data: dict) -> PaymentResponse:
        """
        Handle Stripe webhook events.
        Subscription events: checkout.session.completed, customer.subscription.deleted, invoice.payment_succeeded, invoice.payment_failed, invoice.sent
        """
        try:
            if event_type == 'checkout.session.completed':
                return await self._handle_checkout_completed(event_data)
            elif event_type == 'customer.subscription.deleted':
                return await self._handle_subscription_deleted(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return await self._handle_invoice_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return await self._handle_invoice_payment_failed(event_data)
            elif event_type == 'invoice.sent':
                return await self._handle_invoice_sent(event_data)
            # Legacy one-time payment events (keeping for backwards compatibility)
            elif event_type == 'payment_intent.succeeded':
                return await self._handle_payment_succeeded(event_data)
            elif event_type == 'payment_intent.payment_failed':
                return await self._handle_payment_failed(event_data)
            else:
                return PaymentResponse(
                    success=True,
                    message=f"Unhandled event type: {event_type}"
                )
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"Webhook processing error: {str(e)}"
            )

    async def _handle_checkout_completed(self, session_data: dict) -> PaymentResponse:
        """Handle successful checkout session completion for subscription"""
        session_id = session_data.get('id')
        subscription_id = session_data.get(
            'subscription')  # Get subscription ID
        customer_id = session_data.get('customer')  # Get customer ID
        payment_status = session_data.get('payment_status')
        metadata = session_data.get('metadata', {})
        listing_id = metadata.get('listing_id')
        user_id = metadata.get('user_id')

        payment = await self.payment_service.get_by_session_id(session_id)
        if not payment:
            return PaymentResponse(
                success=False,
                message=f"Payment not found for session: {session_id}"
            )

        # Update payment with subscription_id and customer_id
        if subscription_id:
            payment.subscription_id = subscription_id
            # Store subscription ID as reference
            payment.stripe_payment_intent_id = subscription_id
        if customer_id:
            payment.stripe_customer_id = customer_id
        await payment.save()

        # Store customer_id in user record if not already stored
        if customer_id and user_id:
            user = await self.user_service.get_by_id(user_id)
            if user and not user.stripe_customer_id:
                await self.user_service.update_stripe_customer_id(user_id, customer_id)

        # Update status based on payment_status
        if payment_status == 'paid':
            await self.payment_service.update_payment_status(
                str(payment.id),
                PaymentStatus.Paid
            )

            # Activate the listing and store subscription_id
            if listing_id and subscription_id:
                await self._activate_listing_with_subscription(listing_id, subscription_id)

            return PaymentResponse(
                success=True,
                message="Subscription created successfully! Your listing is now active and will be billed monthly.",
                payment_id=str(payment.id)
            )
        else:
            return PaymentResponse(
                success=True,
                message=f"Checkout completed with status: {payment_status}"
            )

    async def _handle_payment_succeeded(self, payment_intent_data: dict) -> PaymentResponse:
        """Handle successful payment intent"""
        payment_intent_id = payment_intent_data.get('id')
        amount_received = payment_intent_data.get(
            'amount_received', 0) / 100  # Convert from cents
        charges = payment_intent_data.get('charges', {}).get('data', [])

        # Extract payment method details
        last_4_digits = None
        card_brand = None
        payment_method_type = None
        customer_id = payment_intent_data.get('customer')

        if charges:
            charge = charges[0]
            payment_method_details = charge.get('payment_method_details', {})

            if 'card' in payment_method_details:
                card = payment_method_details['card']
                last_4_digits = card.get('last4')
                card_brand = card.get('brand', '').capitalize()
                payment_method_type = PaymentMethodType.Card

                # Check for wallet payments (Apple Pay / Google Pay)
                wallet = card.get('wallet')
                if wallet:
                    wallet_type = wallet.get('type', '')
                    if wallet_type == 'apple_pay':
                        payment_method_type = PaymentMethodType.ApplePay
                    elif wallet_type == 'google_pay':
                        payment_method_type = PaymentMethodType.GooglePay

        # Update payment record
        payment = await self.payment_service.update_payment_details(
            payment_intent_id=payment_intent_id,
            status=PaymentStatus.Paid,
            last_4_digits=last_4_digits,
            card_brand=card_brand,
            payment_method_type=payment_method_type.value if payment_method_type else None,
            stripe_customer_id=customer_id
        )

        if payment:
            return PaymentResponse(
                success=True,
                message="Payment processed successfully! Thank you for your purchase.",
                payment_id=str(payment.id)
            )
        else:
            return PaymentResponse(
                success=False,
                message=f"Payment record not found for intent: {payment_intent_id}"
            )

    async def _handle_payment_failed(self, payment_intent_data: dict) -> PaymentResponse:
        """Handle failed payment intent"""
        payment_intent_id = payment_intent_data.get('id')
        last_payment_error = payment_intent_data.get('last_payment_error', {})
        error_message = last_payment_error.get('message', 'Payment failed')

        payment = await self.payment_service.update_payment_details(
            payment_intent_id=payment_intent_id,
            status=PaymentStatus.Failed,
            error_message=error_message
        )

        if payment:
            return PaymentResponse(
                success=True,
                message=f"Payment failed: {error_message}",
                payment_id=str(payment.id)
            )
        else:
            return PaymentResponse(
                success=False,
                message=f"Payment record not found for intent: {payment_intent_id}"
            )

    async def _handle_subscription_deleted(self, subscription_data: dict) -> PaymentResponse:
        """Handle subscription deletion/cancellation"""
        from py_nyc.web.data_access.models.listing import Listing

        subscription_id = subscription_data.get('id')
        metadata = subscription_data.get('metadata', {})

        # Find listing by subscription_id
        listing = await Listing.find_one(Listing.stripe_subscription_id == subscription_id)

        if listing:
            # Deactivate the listing
            await self._deactivate_listing(str(listing.id))

            return PaymentResponse(
                success=True,
                message=f"Subscription canceled. Listing {listing.id} has been deactivated."
            )
        else:
            return PaymentResponse(
                success=True,
                message=f"Subscription {subscription_id} canceled but no associated listing found."
            )

    async def _handle_invoice_payment_succeeded(self, invoice_data: dict) -> PaymentResponse:
        """Handle successful recurring invoice payment"""
        subscription_id = invoice_data.get('subscription')
        amount_paid = invoice_data.get(
            'amount_paid', 0) / 100  # Convert from cents

        # This is a recurring payment - listing should already be active
        # Just log the successful payment for record keeping
        return PaymentResponse(
            success=True,
            message=f"Recurring payment of ${amount_paid:.2f} succeeded for subscription {subscription_id}"
        )

    async def _handle_invoice_payment_failed(self, invoice_data: dict) -> PaymentResponse:
        """Handle failed recurring invoice payment"""
        from py_nyc.web.data_access.models.listing import Listing

        subscription_id = invoice_data.get('subscription')
        attempt_count = invoice_data.get('attempt_count', 0)

        # Find listing by subscription_id
        listing = await Listing.find_one(Listing.stripe_subscription_id == subscription_id)

        # Stripe will retry failed payments automatically
        # After final retry failure, Stripe will send customer.subscription.deleted event
        # We'll deactivate the listing then

        if listing:
            return PaymentResponse(
                success=True,
                message=f"Recurring payment failed for listing {listing.id} (attempt {attempt_count}). Stripe will retry automatically."
            )
        else:
            return PaymentResponse(
                success=True,
                message=f"Recurring payment failed for subscription {subscription_id} (attempt {attempt_count})."
            )

    async def _handle_invoice_sent(self, invoice_data: dict) -> PaymentResponse:
        """
        Handle Stripe invoice.sent webhook event.
        Records that Stripe sent an invoice email to the customer.
        """
        if not self.email_logic:
            # Email logic not initialized, skip recording
            return PaymentResponse(
                success=True,
                message="Email logic not initialized, skipping invoice email recording"
            )

        invoice_id = invoice_data.get('id')
        customer_email = invoice_data.get('customer_email')
        subscription_id = invoice_data.get('subscription')
        customer_id = invoice_data.get('customer')

        if not invoice_id or not customer_email:
            return PaymentResponse(
                success=False,
                message="Missing invoice_id or customer_email in webhook data"
            )

        # Get user_id from customer_id if available
        user_id = None
        if customer_id:
            user = await self.user_service.get_by_id(customer_id)
            if user:
                user_id = str(user.id)

        # Record that Stripe sent this invoice email
        result = await self.email_logic.record_stripe_invoice_email(
            to_email=customer_email,
            stripe_invoice_id=invoice_id,
            stripe_subscription_id=subscription_id,
            user_id=user_id
        )

        if result.success:
            return PaymentResponse(
                success=True,
                message=f"Recorded Stripe invoice email for {customer_email}"
            )
        else:
            return PaymentResponse(
                success=False,
                message=f"Failed to record invoice email: {result.message}"
            )

    async def _count_user_active_listings(self, user_id: PydanticObjectId) -> int:
        """Count user's active listings"""
        # Use listing service to count active listings for the user
        result = await self.listing_service.get_user_listings(user_id, offset=0, limit=1)
        return result.total

    async def _activate_listing_with_subscription(self, listing_id: str, subscription_id: str) -> None:
        """Activate a listing and store subscription ID after successful payment"""
        from py_nyc.web.data_access.models.listing import Listing
        from datetime import datetime, timezone

        listing = await Listing.get(listing_id)
        if listing:
            listing.active = True
            listing.stripe_subscription_id = subscription_id  # Store subscription ID
            listing.updated_at = datetime.now(timezone.utc)
            await listing.save()

    async def _deactivate_listing(self, listing_id: str) -> None:
        """Deactivate a listing (called when subscription is canceled or payment fails)"""
        from py_nyc.web.data_access.models.listing import Listing
        from datetime import datetime, timezone

        listing = await Listing.get(listing_id)
        if listing:
            listing.active = False
            listing.updated_at = datetime.now(timezone.utc)
            await listing.save()

    async def get_user_payments(self, user_id: PydanticObjectId, page: int = 1, per_page: int = 20):
        """Get user's payment history"""
        offset = (page - 1) * per_page
        return await self.payment_service.get_user_payments(user_id, offset, per_page)

    async def cancel_subscription(self, subscription_id: str) -> PaymentResponse:
        """
        Cancel a Stripe subscription.
        This is called when a user deactivates a listing.
        """
        try:
            # Cancel the subscription in Stripe
            # at_period_end=False means cancel immediately
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False  # Cancel immediately
            )

            # Actually delete/cancel it
            canceled_subscription = stripe.Subscription.cancel(subscription_id)

            return PaymentResponse(
                success=True,
                message="Subscription canceled successfully"
            )
        except stripe.error.StripeError as e:
            return PaymentResponse(
                success=False,
                message=f"Failed to cancel subscription: {str(e)}"
            )
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"An unexpected error occurred: {str(e)}"
            )

    def get_listing_price_info(self) -> dict:
        """
        Fetch the listing price information from Stripe.
        Returns price amount and currency.
        """
        try:
            price = stripe.Price.retrieve(
                self.settings.stripe_listing_price_id)
            return {
                "amount": price.unit_amount / 100,  # Convert from cents to dollars
                "currency": price.currency,
                "recurring": price.recurring.interval if price.recurring else None
            }
        except stripe.error.StripeError as e:
            # Fallback to default if Stripe API fails
            return {
                "amount": 5.0,
                "currency": "usd",
                "recurring": "month"
            }

    async def get_subscription_info(
        self,
        user_id: PydanticObjectId
    ) -> SubscriptionInfoResponse:
        """
        Get user's subscription/billing information from Stripe.
        Makes ONE API call to fetch all subscriptions for the customer.
        """
        # Get user's active listings count
        active_listings_count = await self._count_user_active_listings(user_id)

        # Get current price from Stripe
        price_info = self.get_listing_price_info()
        price_per_listing = price_info['amount']
        currency = price_info['currency']

        # Get user's stripe_customer_id
        user = await self.user_service.get_by_id(str(user_id))

        paid_listings_count = 0
        monthly_charge = 0.0

        if user and user.stripe_customer_id:
            try:
                # ✅ ONE API CALL: Fetch all active subscriptions for this customer
                subscriptions = stripe.Subscription.list(
                    customer=user.stripe_customer_id,
                    status='active',
                    limit=100  # Adjust if user can have more than 100 subscriptions
                )

                # Calculate total from all active subscriptions
                # Iterate directly over the list object (works with Stripe SDK)
                print(len(subscriptions.data))
                for subscription in subscriptions.auto_paging_iter():
                    paid_listings_count += 1
                    # Use dictionary access for Stripe objects to avoid attribute errors
                    items_list = subscription.get('items', {}).get('data', [])
                    for item in items_list:
                        unit_amount = item.get(
                            'price', {}).get('unit_amount', 0)
                        if unit_amount:
                            amount = unit_amount / 100
                            monthly_charge += amount

            except stripe.error.StripeError as e:
                # Log error but return default values
                print(e)
                pass
            except Exception as e:
                print(e)
                # Catch any other errors (e.g., attribute errors)
                pass

        return SubscriptionInfoResponse(
            active_listings_count=active_listings_count,
            monthly_charge=monthly_charge,
            price_per_listing=price_per_listing,
            currency=currency,
            free_listings_limit=self.FREE_LISTINGS_LIMIT,
            paid_listings_count=paid_listings_count
        )
