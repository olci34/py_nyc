from typing import Optional, TYPE_CHECKING
from py_nyc.web.data_access.models.user import User
from py_nyc.web.data_access.models.password_reset import (
    PasswordResetToken,
    RequestPasswordResetResponse,
    ResetPasswordResponse
)
from py_nyc.web.data_access.services.user_service import UserService
from py_nyc.web.data_access.services.password_reset_service import PasswordResetService
from py_nyc.web.utils.hashing import verify_pwd, bcrypt_pwd
from datetime import datetime, timezone

if TYPE_CHECKING:
    from py_nyc.web.core.email_logic import EmailLogic


class UsersLogic:
  def __init__(
      self,
      user_service: UserService,
      password_reset_service: Optional[PasswordResetService] = None,
      email_logic: Optional["EmailLogic"] = None
  ):
    self.user_service = user_service
    self.password_reset_service = password_reset_service
    self.email_logic = email_logic

  async def authenticate_user(self, email: str, password: str) -> User | bool:
    user = await self.find_by_email(email)
    if not user:
      return False

    # OAuth users don't have passwords
    if not user.password:
      return False

    if not verify_pwd(user.password, password):
      return False

    return user

  async def register(self, user: User):
    new_user = await self.user_service.register(user)

    # Send welcome email if email logic is available
    if self.email_logic and new_user.email and new_user.first_name:
      try:
        await self.email_logic.send_welcome_email(
          to_email=new_user.email,
          to_name=new_user.first_name,
          user_id=str(new_user.id)
        )
      except Exception as e:
        # Log error but don't fail registration
        print(f"Failed to send welcome email: {str(e)}")

    return new_user

  async def find_by_email(self, email: str) -> User | None:
    return await self.user_service.get_by_email(email)

  async def find_by_google_id(self, google_id: str) -> User | None:
    return await self.user_service.get_by_google_id(google_id)

  async def authenticate_or_register_google_user(
    self, email: str, first_name: str, last_name: str, google_id: str, visitor_id: str | None
  ) -> User:
    """
    Authenticate or register a user via Google OAuth.

    Logic:
    1. Try to find user by google_id
    2. If not found, try to find by email
    3. If found by email but no google_id, update user with google_id
    4. If not found at all, create new user

    Returns the authenticated/created user.
    """
    # 1. Look up user by google_id
    user = await self.find_by_google_id(google_id)

    if user:
      # User found by google_id, return existing user
      return user

    # 2. Look up by email
    user = await self.find_by_email(email)

    if user:
      # 3. User exists with email but no google_id, update it
      user = await self.user_service.update_google_id(str(user.id), google_id)
      return user

    # 4. Create new user (no password for OAuth users)
    new_user = User(
      email=email,
      first_name=first_name,
      last_name=last_name,
      google_id=google_id,
      visitor_id=visitor_id,
      password=None  # OAuth users don't have passwords
    )
    created_user = await self.register(new_user)

    # Welcome email is already sent in register() method
    return created_user

  async def request_password_reset(
      self,
      email: str,
      ip_address: Optional[str] = None,
      user_agent: Optional[str] = None,
      frontend_url: str = "http://localhost:3000"
  ) -> RequestPasswordResetResponse:
    """
    Request a password reset for a user.

    Security measures:
    - Rate limiting: Max 3 requests per 15 minutes per email
    - Tokens expire in 30 minutes
    - Tokens are single-use
    - Tokens are hashed in database
    - Always return success message (don't reveal if email exists)
    """
    if not self.password_reset_service or not self.email_logic:
      return RequestPasswordResetResponse(
          success=False,
          message="Password reset service not configured"
      )

    try:
      # Rate limiting: Check recent requests (max 3 per 15 minutes)
      recent_count = await self.password_reset_service.count_recent_requests(email, minutes=15)
      if recent_count >= 3:
        # Don't reveal rate limit to user, just return generic message
        return RequestPasswordResetResponse(
            success=True,
            message="If an account exists with this email, you will receive password reset instructions."
        )

      # Find user by email
      user = await self.find_by_email(email)

      if not user:
        # Don't reveal that user doesn't exist (security best practice)
        # Return success anyway to prevent email enumeration attacks
        return RequestPasswordResetResponse(
            success=True,
            message="If an account exists with this email, you will receive password reset instructions."
        )

      # OAuth users cannot reset passwords
      if not user.password:
        # Send email explaining they need to use Google sign-in
        if self.email_logic:
          try:
            await self.email_logic.send_oauth_password_attempt_email(
              to_email=email,
              to_name=user.first_name,
              user_id=str(user.id)
            )
          except Exception as e:
            print(f"Failed to send OAuth password attempt email: {str(e)}")

        # Return generic success message (security: don't reveal OAuth status)
        return RequestPasswordResetResponse(
            success=True,
            message="If an account exists with this email, you will receive password reset instructions."
        )

      # Invalidate all existing tokens for this user
      await self.password_reset_service.invalidate_user_tokens(str(user.id))

      # Generate new token
      token = PasswordResetToken.generate_token()
      token_hash = PasswordResetToken.hash_token(token)

      # Create token record in database
      reset_token = PasswordResetToken(
          user_id=str(user.id),
          token_hash=token_hash,
          email=email,
          expires_at=PasswordResetToken.create_expiry(minutes=30),
          ip_address=ip_address,
          user_agent=user_agent
      )
      await self.password_reset_service.create(reset_token)

      # Send email with reset link
      await self.email_logic.send_password_reset_email(
          to_email=email,
          to_name=user.first_name,
          reset_token=token,  # Send plaintext token in email
          user_id=str(user.id),
          frontend_url=frontend_url
      )

      return RequestPasswordResetResponse(
          success=True,
          message="If an account exists with this email, you will receive password reset instructions."
      )

    except Exception as e:
      print(f"Error requesting password reset: {str(e)}")
      return RequestPasswordResetResponse(
          success=False,
          message="An error occurred. Please try again later."
      )

  async def reset_password(
      self,
      token: str,
      new_password: str
  ) -> ResetPasswordResponse:
    """
    Reset a user's password using a valid token.

    Security measures:
    - Token must exist, not be used, and not be expired
    - Password is hashed before storing
    - Token is marked as used after successful reset
    - All other tokens for the user are invalidated
    """
    if not self.password_reset_service:
      return ResetPasswordResponse(
          success=False,
          message="Password reset service not configured"
      )

    try:
      # Hash the token to look it up in database
      token_hash = PasswordResetToken.hash_token(token)

      # Find valid token
      reset_token = await self.password_reset_service.get_valid_token_by_hash(token_hash)

      if not reset_token:
        return ResetPasswordResponse(
            success=False,
            message="Invalid or expired reset token. Please request a new password reset."
        )

      # Get user
      user = await self.user_service.get_by_id(reset_token.user_id)

      if not user:
        return ResetPasswordResponse(
            success=False,
            message="User not found"
        )

      # Validate password strength (basic check - can be enhanced)
      if len(new_password) < 8:
        return ResetPasswordResponse(
            success=False,
            message="Password must be at least 8 characters long"
        )

      # Hash and update password
      hashed_password = bcrypt_pwd(new_password)
      user.password = hashed_password
      user.updated_at = datetime.now(timezone.utc)
      await user.save()

      # Mark token as used
      await reset_token.mark_as_used()

      # Invalidate all other tokens for this user
      await self.password_reset_service.invalidate_user_tokens(str(user.id))

      return ResetPasswordResponse(
          success=True,
          message="Password reset successfully. You can now log in with your new password."
      )

    except Exception as e:
      print(f"Error resetting password: {str(e)}")
      return ResetPasswordResponse(
          success=False,
          message="An error occurred. Please try again later."
      )

  async def change_password(
      self,
      user_id: str,
      current_password: str,
      new_password: str
  ) -> ResetPasswordResponse:
    """
    Change password for an authenticated user.

    Security measures:
    - Requires current password verification
    - New password must meet strength requirements
    - Password is hashed before storing
    """
    try:
      # Get user
      user = await self.user_service.get_by_id(user_id)

      if not user:
        return ResetPasswordResponse(
            success=False,
            message="User not found"
        )

      # OAuth users don't have passwords
      if not user.password:
        return ResetPasswordResponse(
            success=False,
            message="Password change not available for OAuth users. Please use your Google account."
        )

      # Verify current password
      if not verify_pwd(user.password, current_password):
        return ResetPasswordResponse(
            success=False,
            message="Current password is incorrect"
        )

      # Validate new password strength
      if len(new_password) < 8:
        return ResetPasswordResponse(
            success=False,
            message="Password must be at least 8 characters long"
        )

      # Prevent reusing the same password
      if verify_pwd(user.password, new_password):
        return ResetPasswordResponse(
            success=False,
            message="New password must be different from current password"
        )

      # Hash and update password
      hashed_password = bcrypt_pwd(new_password)
      user.password = hashed_password
      user.updated_at = datetime.now(timezone.utc)
      await user.save()

      # Invalidate all password reset tokens for this user (if service available)
      if self.password_reset_service:
        await self.password_reset_service.invalidate_user_tokens(str(user.id))

      return ResetPasswordResponse(
          success=True,
          message="Password changed successfully"
      )

    except Exception as e:
      print(f"Error changing password: {str(e)}")
      return ResetPasswordResponse(
          success=False,
          message="An error occurred. Please try again later."
      )
