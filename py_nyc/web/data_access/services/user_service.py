from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.data_access.models.user import User
from datetime import datetime, timezone

class UserService:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.users_collection = db.get_collection('users')

    async def register(self, user: User) -> User:
        return await user.create()

    async def get_by_email(self, email: str) -> User | None:
        return await User.find_one(User.email == email)

    async def get_by_google_id(self, google_id: str) -> User | None:
        return await User.find_one(User.google_id == google_id)

    async def update_google_id(self, user_id: str, google_id: str) -> User | None:
        user = await User.get(user_id)
        if user:
            user.google_id = google_id
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
        return user

    async def update_stripe_customer_id(self, user_id: str, stripe_customer_id: str) -> User | None:
        user = await User.get(user_id)
        if user:
            user.stripe_customer_id = stripe_customer_id
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        return await User.get(user_id)

    async def update_cookie_consent(
        self,
        user_id: str,
        accepted: bool,
        ip_address: str | None,
        user_agent: str | None
    ) -> User | None:
        user = await User.get(user_id)
        if user:
            user.cookie_consent_accepted = accepted
            user.cookie_consent_accepted_at = datetime.now(timezone.utc)
            user.cookie_consent_ip_address = ip_address
            user.cookie_consent_user_agent = user_agent
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
        return user

    async def schedule_for_deletion(self, user_id: str) -> User | None:
        """Schedule a user account for deletion with a 7-day grace period"""
        user = await User.get(user_id)
        if user:
            user.scheduled_for_deletion_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
        return user

    async def cancel_deletion(self, user_id: str) -> User | None:
        """Cancel a scheduled account deletion (when user signs back in)"""
        user = await User.get(user_id)
        if user:
            user.scheduled_for_deletion_at = None
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
        return user

    async def get_users_scheduled_for_deletion(self, days: int = 7) -> list[User]:
        """Get all users scheduled for deletion past the grace period"""
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        users = await User.find(
            User.scheduled_for_deletion_at != None,
            User.scheduled_for_deletion_at <= cutoff_date
        ).to_list()
        return users

    async def permanently_delete(self, user_id: str) -> bool:
        """Permanently delete a user account"""
        user = await User.get(user_id)
        if user:
            await user.delete()
            return True
        return False
