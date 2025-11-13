from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import BaseModel

from py_nyc.web.core.config import Settings, get_settings


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta | None = None, settings: Settings = None):
    if settings is None:
        settings = get_settings()

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str, creds_exception: HTTPException, settings: Settings = None) -> TokenData:
    if settings is None:
        settings = get_settings()

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=settings.algorithm)
        email = payload.get("email")
        id = payload.get("id")

        if email is None or id is None:
            raise creds_exception

        return TokenData(id=id, email=email)

    except jwt.InvalidTokenError:
        raise creds_exception


def get_user_info(token: str = Depends(oauth2_scheme)) -> TokenData:
    cred_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"}
    )

    return verify_token(token, cred_exception)
