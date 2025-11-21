from typing import Optional
from datetime import datetime, timezone, timedelta
from beanie import Document
from pydantic import BaseModel, Field
import secrets
import hashlib


class PasswordResetToken(Document):
    """
    Password reset token model.
    Stores hashed tokens for security - never store plaintext tokens.
    """
    user_id: str  # User who requested the reset
    token_hash: str  # SHA256 hash of the token (never store plaintext)
    email: str  # Email of the user (for verification)

    # Expiry and usage tracking
    expires_at: datetime
    used: bool = False
    used_at: Optional[datetime] = None

    # Metadata
    ip_address: Optional[str] = None  # IP that requested the reset (for audit)
    user_agent: Optional[str] = None  # User agent (for audit)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "password_reset_tokens"
        indexes = [
            "token_hash",
            "user_id",
            "email",
            "expires_at"
        ]

    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure random token.
        Returns 32 bytes = 64 hex characters
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token using SHA256.
        We store hashed tokens in DB for security.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def create_expiry(minutes: int = 30) -> datetime:
        """Create expiry datetime (default 30 minutes from now)"""
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)

    def is_valid(self) -> bool:
        """Check if token is still valid (not expired and not used)"""
        now = datetime.now(timezone.utc)
        return not self.used and self.expires_at > now

    async def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.used_at = datetime.now(timezone.utc)
        await self.save()


class RequestPasswordResetRequest(BaseModel):
    """Request to initiate password reset"""
    email: str


class RequestPasswordResetResponse(BaseModel):
    """Response after requesting password reset"""
    success: bool
    message: str


class ResetPasswordRequest(BaseModel):
    """Request to reset password with token"""
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    """Response after resetting password"""
    success: bool
    message: str
