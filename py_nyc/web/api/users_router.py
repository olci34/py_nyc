from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel
from py_nyc.web.api.models.login_response import AuthUser, LoginResponse
from py_nyc.web.data_access.models.user import User
from py_nyc.web.dependencies import UsersLogicDep
from py_nyc.web.utils.auth import create_access_token
from py_nyc.web.utils.hashing import bcrypt_pwd

class SignupData(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class LoginData(BaseModel):
    email: str
    password: str


users_router = APIRouter(prefix='/users')

@users_router.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(users_logic: UsersLogicDep, signup_data: SignupData = Body()):
  # Check if user with same email exists
  user = await users_logic.find_by_email(signup_data.email)
  if user is not None:
      return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
  
  # Hash Password
  hashed_pwd = bcrypt_pwd(signup_data.password)
  # Register User
  user = User(email=signup_data.email, password=hashed_pwd, first_name=signup_data.first_name, last_name=signup_data.last_name)
  await users_logic.register(user)
  return True


@users_router.post('/login', response_model=LoginResponse)
async def login(users_logic: UsersLogicDep, login_data: LoginData = Body()):
  user = await users_logic.authenticate_user(email=login_data.email, password=login_data.password)
  if not user:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

  token = create_access_token(data={"sub": str(user.id), "email": user.email})
  auth_user = AuthUser(id=user.email, first_name=user.first_name, last_name=user.last_name)
  return LoginResponse(user=auth_user, access_token=token, token_type='bearer')
  

  

