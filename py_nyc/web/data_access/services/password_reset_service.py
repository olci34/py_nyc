from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.data_access.models.password_reset import PasswordResetToken
from datetime import datetime, timezone, timedelta
from typing import Optional


class PasswordResetService:
    """
    Data access service for PasswordResetToken model.
    Handles all database operations related to password reset tokens.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.password_reset_tokens_collection = db.get_collection('password_reset_tokens')

    async def create(self, token: PasswordResetToken) -> PasswordResetToken:
        """Create a new password reset token"""
        return await token.create()

    async def get_by_token_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Get token by hash"""
        return await PasswordResetToken.find_one(PasswordResetToken.token_hash == token_hash)

    async def get_valid_token_by_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Get a valid (not used and not expired) token by hash"""
        now = datetime.now(timezone.utc)
        return await PasswordResetToken.find_one(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > now
        )

    async def invalidate_user_tokens(self, user_id: str):
        """
        Invalidate all existing tokens for a user.
        Called when creating a new reset token or after successful password reset.
        """
        tokens = await PasswordResetToken.find(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used == False
        ).to_list()

        for token in tokens:
            await token.mark_as_used()

    async def count_recent_requests(self, email: str, minutes: int = 15) -> int:
        """
        Count how many password reset requests were made for this email
        in the last N minutes. Used for rate limiting.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        count = await PasswordResetToken.find(
            PasswordResetToken.email == email,
            PasswordResetToken.created_at > cutoff
        ).count()
        return count

    async def cleanup_expired_tokens(self):
        """
        Delete expired tokens (cleanup job).
        Call this periodically to keep the database clean.
        """
        now = datetime.now(timezone.utc)
        expired_tokens = await PasswordResetToken.find(
            PasswordResetToken.expires_at < now
        ).to_list()

        for token in expired_tokens:
            await token.delete()

        return len(expired_tokens)
