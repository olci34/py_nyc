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

    # OAuth users don't have passwords
    if not user.password:
      return False

    if not verify_pwd(user.password, password):
      return False

    return user

  async def register(self, user: User):
    new_user = await self.user_service.register(user)
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
    return await self.register(new_user)
