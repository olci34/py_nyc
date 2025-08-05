from motor.motor_asyncio import AsyncIOMotorDatabase
from py_nyc.web.data_access.models.user import User

class UserService:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.users_collection = db.get_collection('users')

    async def register(self, user: User) -> User:
        return await user.create()
    
    async def get_by_email(self, email: str) -> User | None:
        return await User.find_one(User.email == email)

      