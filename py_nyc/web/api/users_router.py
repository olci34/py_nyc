from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from py_nyc.web.core import users_logic
from py_nyc.web.data_access.models.user import User, UserResponse
from py_nyc.web.dependencies import UsersLogicDep
from py_nyc.web.utils.auth import create_access_token
from py_nyc.web.utils.hashing import bcrypt_pwd, verify_pwd

class SignupData(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class LoginData(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

users_router = APIRouter(prefix='/users')

@users_router.post('/signup')
async def signup(signup_data: SignupData, users_logic: UsersLogicDep):
  print(signup_data)
  # Check if user with same email exists
  user = await users_logic.find_by_email(signup_data.email)
  if user is not None:
      return False
  # Hash Password
  hashed_pwd = bcrypt_pwd(signup_data.password)
  # Register User
  user = User(email=signup_data.email, password=hashed_pwd, first_name=signup_data.first_name, last_name=signup_data.last_name)
  new_user = await users_logic.register(user)
  return {'created': str(new_user.id)}


@users_router.post('/login', response_model=Token)
async def login(login_data: Annotated[OAuth2PasswordRequestForm, Depends()], users_logic: UsersLogicDep):
  user = await users_logic.authenticate_user(email=login_data.username, password=login_data.password)
  if not user:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

  #return TokenData
  token = create_access_token(data={"sub": str(user.id), "email": user.email})
  return Token(access_token=token, token_type='bearer')
  

  

