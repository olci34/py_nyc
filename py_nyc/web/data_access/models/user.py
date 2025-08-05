from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr


class User(Document):
  email: EmailStr = Indexed(unique=True)
  password: str
  first_name: str
  last_name: str

  class Settings:
    name = "users"


class UserResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str