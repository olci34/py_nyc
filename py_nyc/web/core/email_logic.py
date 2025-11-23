import resend
from resend import Emails
from typing import Optional
from py_nyc.web.data_access.models.email import (
    Email,
    EmailType,
    EmailStatus,
    SendEmailRequest,
    SendEmailResponse
)
from py_nyc.web.data_access.services.email_service import EmailService
from py_nyc.web.core.config import Settings


class EmailLogic:
    """
    Business logic for email operations.
    Handles sending emails via Resend and persisting metadata.
    """

    def __init__(self, email_service: EmailService, settings: Settings):
        self.email_service = email_service
        self.settings = settings
        # Initialize Resend with API key if configured
        if settings.resend_api_key:
            resend.api_key = settings.resend_api_key

    def _is_resend_configured(self) -> bool:
        """Check if Resend API is configured."""
        return self.settings.resend_api_key is not None

    async def _persist_email_record(
        self,
        request: SendEmailRequest,
        status: EmailStatus,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Email:
        """
        Persist email record to database.

        Args:
            request: Original email request
            status: Email status (SENT or FAILED)
            provider_message_id: ID from email provider (if successful)
            error_message: Error message (if failed)

        Returns:
            Created email record
        """
        email_record = Email(
            to=request.to,
            to_name=request.to_name,
            subject=request.subject,
            email_type=request.email_type,
            from_email=self.settings.resend_from_email,
            from_name=self.settings.resend_from_name,
            user_id=request.user_id,
            template_data=request.template_data,
            status=status,
            provider_message_id=provider_message_id,
            error_message=error_message
        )
        return await self.email_service.create(email_record)

    async def _send_template_email(
        self,
        request: SendEmailRequest,
        template_id: str
    ) -> SendEmailResponse:
        """
        Send email using Resend template.

        Args:
            request: Email request with template variables
            template_id: Resend template ID

        Returns:
            SendEmailResponse with success status
        """
        if not self._is_resend_configured():
            print("Resend API key not configured. Email sending is disabled.")
            return SendEmailResponse(
                success=False,
                message="Email service not configured"
            )

        try:
            # Build SendParams for template email
            params = Emails.SendParams({
                "to": [request.to],
                "template": {
                    "id": template_id,
                    "variables": request.template_data
                }
            })

            # Send email via Resend
            response = resend.Emails.send(params)

            # Persist successful email to database
            created_email = await self._persist_email_record(
                request=request,
                status=EmailStatus.SENT,
                provider_message_id=response.get('id') if isinstance(response, dict) else None
            )

            return SendEmailResponse(
                success=True,
                message="Email sent successfully",
                email_id=str(created_email.id),
                provider_message_id=response.get('id') if isinstance(response, dict) else None
            )

        except Exception as e:
            # Persist failed email to database
            created_email = await self._persist_email_record(
                request=request,
                status=EmailStatus.FAILED,
                error_message=str(e)
            )

            return SendEmailResponse(
                success=False,
                message=f"Failed to send email: {str(e)}",
                email_id=str(created_email.id)
            )

    async def _send_html_email(
        self,
        request: SendEmailRequest
    ) -> SendEmailResponse:
        """
        Send email using HTML content.

        Args:
            request: Email request with HTML content

        Returns:
            SendEmailResponse with success status
        """
        if not self._is_resend_configured():
            print("Resend API key not configured. Email sending is disabled.")
            return SendEmailResponse(
                success=False,
                message="Email service not configured"
            )

        try:
            # Build SendParams for HTML email
            params = Emails.SendParams({
                "to": [request.to],
                "from": f"{self.settings.resend_from_name} <{self.settings.resend_from_email}>",
                "subject": request.subject,
                "html": request.html
            })

            # Send email via Resend
            response = resend.Emails.send(params)

            # Persist successful email to database
            created_email = await self._persist_email_record(
                request=request,
                status=EmailStatus.SENT,
                provider_message_id=response.get('id') if isinstance(response, dict) else None
            )

            return SendEmailResponse(
                success=True,
                message="Email sent successfully",
                email_id=str(created_email.id),
                provider_message_id=response.get('id') if isinstance(response, dict) else None
            )

        except Exception as e:
            # Persist failed email to database
            created_email = await self._persist_email_record(
                request=request,
                status=EmailStatus.FAILED,
                error_message=str(e)
            )

            return SendEmailResponse(
                success=False,
                message=f"Failed to send email: {str(e)}",
                email_id=str(created_email.id)
            )

    async def send_welcome_email(
        self,
        to_email: str,
        to_name: str,
        user_id: str
    ) -> SendEmailResponse:
        """
        Send welcome email using Resend template 'welcomeemail_en'.
        Template variables: name, root_url
        """
        # Get frontend URL from settings (first CORS origin)
        frontend_url = self.settings.cors_origins.split(",")[0]

        template_data = {
            "name": to_name,
            "root_url": frontend_url
        }

        request = SendEmailRequest(
            to=to_email,
            to_name=to_name,
            subject="Welcome to TLC Shift!",
            html="",
            email_type=EmailType.WELCOME,
            user_id=user_id,
            template_data=template_data
        )

        return await self._send_template_email(request, self.settings.resend_template_welcome)

    async def send_password_reset_email(
        self,
        to_email: str,
        to_name: Optional[str],
        reset_token: str,
        user_id: str,
        frontend_url: str = "http://localhost:3000"
    ) -> SendEmailResponse:
        """
        Send password reset email using Resend template 'pwdreset_en'.
        Template variables: name, expiry_time, reset_link
        """
        # Build reset URL for frontend
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"

        # Prepare template variables
        display_name = to_name if to_name else "friend"
        expiry_minutes = 30  # Token expires in 30 minutes

        template_data = {
            "name": display_name,
            "expiry_time": f"{expiry_minutes} minutes",
            "reset_link": reset_url
        }

        request = SendEmailRequest(
            to=to_email,
            to_name=to_name,
            subject="Reset Your Password - TLC App",
            html="",
            email_type=EmailType.PASSWORD_RESET,
            user_id=user_id,
            template_data=template_data
        )

        return await self._send_template_email(request, self.settings.resend_template_password_reset)

    async def send_waitlist_confirmation_email(
        self,
        to_email: str,
        to_name: Optional[str] = None
    ) -> SendEmailResponse:
        """
        Send waitlist confirmation email using Resend template 'waitlist_en'.
        Template variables: root_url
        """
        # Get frontend URL from settings (first CORS origin)
        frontend_url = self.settings.cors_origins.split(",")[0]

        template_data = {
            "root_url": frontend_url
        }

        request = SendEmailRequest(
            to=to_email,
            to_name=to_name,
            subject="Welcome to the Waitlist - TLC Shift",
            html="",
            email_type=EmailType.WAITLIST_CONFIRMATION,
            template_data=template_data
        )

        return await self._send_template_email(request, self.settings.resend_template_waitlist)

    async def send_oauth_password_attempt_email(
        self,
        to_email: str,
        to_name: Optional[str],
        user_id: str
    ) -> SendEmailResponse:
        """
        Send email to OAuth users who try to reset password.
        Explains they signed up with Google and should use Google sign-in.
        Template variables: name, root_url, login_url
        """
        # Get frontend URL from settings (first CORS origin)
        frontend_url = self.settings.cors_origins.split(",")[0]
        login_url = f"{frontend_url}/signup-login"

        display_name = to_name if to_name else "there"

        template_data = {
            "name": display_name,
            "root_url": frontend_url,
            "login_url": login_url
        }

        request = SendEmailRequest(
            to=to_email,
            to_name=to_name,
            subject="About Your TLC Shift Account",
            html="",
            email_type=EmailType.OAUTH_PASSWORD_ATTEMPT,
            user_id=user_id,
            template_data=template_data
        )

        return await self._send_template_email(request, self.settings.resend_template_oauth_password_attempt)

    async def record_stripe_invoice_email(
        self,
        to_email: str,
        stripe_invoice_id: str,
        stripe_subscription_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> SendEmailResponse:
        """
        Record that Stripe sent an invoice email to a customer.
        We don't send this email ourselves - Stripe does it.
        We just track it in our database for audit purposes.
        """
        try:
            # Check if we already recorded this invoice email
            existing = await self.email_service.get_by_stripe_invoice(stripe_invoice_id)
            if existing:
                return SendEmailResponse(
                    success=True,
                    message="Invoice email already recorded",
                    email_id=str(existing.id)
                )

            # Create email record (status: SENT, since Stripe already sent it)
            email_record = Email(
                to=to_email,
                subject=f"Invoice from TLC App",
                email_type=EmailType.STRIPE_INVOICE,
                from_email="Stripe <noreply@stripe.com>",
                from_name="Stripe",
                provider="stripe",
                status=EmailStatus.SENT,
                stripe_invoice_id=stripe_invoice_id,
                stripe_subscription_id=stripe_subscription_id,
                user_id=user_id
            )
            created_email = await self.email_service.create(email_record)

            return SendEmailResponse(
                success=True,
                message="Stripe invoice email recorded",
                email_id=str(created_email.id)
            )

        except Exception as e:
            return SendEmailResponse(
                success=False,
                message=f"Error recording invoice email: {str(e)}"
            )
