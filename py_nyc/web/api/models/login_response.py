from pydantic import BaseModel

class AuthUser(BaseModel):
  id: str
  first_name: str
  last_name: str
  email: str

class LoginResponse(BaseModel):
  user: AuthUser
  access_token: str
  token_type: str
