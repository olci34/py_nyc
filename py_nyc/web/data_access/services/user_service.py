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
