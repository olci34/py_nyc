from py_nyc.web.data_access.models.user import User
from py_nyc.web.data_access.services.user_service import UserService
from py_nyc.web.utils.hashing import verify_pwd


class UsersLogic:
  def __init__(self, user_service: UserService):
    self.user_service = user_service

  async def authenticate_user(self, email: str, password: str) -> User | bool:
    user = await self.find_by_email(email)
    if not user:
      return False
    
    if not verify_pwd(user.password, password):
      return False
    
    return user

  async def register(self, user: User):
    new_user = await self.user_service.register(user)
    return new_user

  async def find_by_email(self, email: str) -> User | None:
    return await self.user_service.get_by_email(email)
  