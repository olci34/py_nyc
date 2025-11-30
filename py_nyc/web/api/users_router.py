from typing import Optional
from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Body, HTTPException, status, Depends, Request
from pydantic import BaseModel
from py_nyc.web.api.models.login_response import AuthUser, LoginResponse
from py_nyc.web.data_access.models.user import User
from py_nyc.web.data_access.models.password_reset import (
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ChangePasswordRequest
)
from py_nyc.web.dependencies import UsersLogicDep
from py_nyc.web.utils.auth import create_access_token, get_user_info
from py_nyc.web.utils.hashing import bcrypt_pwd
from py_nyc.web.core.config import get_settings


class SignupData(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    visitor_id: Optional[str] = None
    legal_consent_accepted: bool


class LoginData(BaseModel):
    email: str
    password: str


class GoogleAuthData(BaseModel):
    email: str
    first_name: str
    last_name: str
    google_id: str
    visitor_id: Optional[str] = None
    legal_consent_accepted: Optional[bool] = None


class CookieConsentData(BaseModel):
    accepted: bool


users_router = APIRouter(prefix='/users')


@users_router.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(request: Request, users_logic: UsersLogicDep, signup_data: SignupData = Body()):
    # Validate consent
    if not signup_data.legal_consent_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the Terms of Service and Privacy Policy to create an account",
        )

    # Check if user with same email exists
    user = await users_logic.find_by_email(signup_data.email)
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Hash Password
    hashed_pwd = bcrypt_pwd(signup_data.password)

    # Get current timestamp for consent tracking
    now = datetime.now(timezone.utc)

    # Get client IP address and user agent for consent audit trail
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Register User
    user = User(
        email=signup_data.email,
        password=hashed_pwd,
        first_name=signup_data.first_name,
        last_name=signup_data.last_name,
        visitor_id=signup_data.visitor_id,
        legal_consent_accepted=signup_data.legal_consent_accepted,
        legal_consent_accepted_at=now if signup_data.legal_consent_accepted else None,
        legal_consent_ip_address=ip_address if signup_data.legal_consent_accepted else None,
        legal_consent_user_agent=user_agent if signup_data.legal_consent_accepted else None,
        legal_consent_version="1.0"
    )
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

    token = create_access_token(data={"id": str(
        user.id), "email": user.email}, expires_delta=timedelta(minutes=60))
    auth_user = AuthUser(id=str(user.id), first_name=user.first_name,
                         last_name=user.last_name, email=user.email)
    return LoginResponse(user=auth_user, access_token=token, token_type='Bearer')


@users_router.post('/google-auth', response_model=LoginResponse)
async def google_auth(request: Request, users_logic: UsersLogicDep, google_data: GoogleAuthData = Body()):
    """
    Authenticate or register a user via Google OAuth.

    This endpoint will:
    1. Check if user with google_id exists
    2. If not, check if user with email exists
    3. If user exists by email, link google_id to the account
    4. If user doesn't exist at all, create new user
    5. Return user data and access token
    """
    try:
        # Get client IP address and user agent for consent audit trail
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        user = await users_logic.authenticate_or_register_google_user(
            email=google_data.email,
            first_name=google_data.first_name,
            last_name=google_data.last_name,
            google_id=google_data.google_id,
            visitor_id=google_data.visitor_id,
            legal_consent_accepted=google_data.legal_consent_accepted,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Generate access token
        token = create_access_token(
            data={"id": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=60)
        )

        # Create auth user response
        auth_user = AuthUser(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email
        )

        return LoginResponse(user=auth_user, access_token=token, token_type='Bearer')

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate with Google: {str(e)}"
        )


@users_router.post('/request-password-reset', response_model=RequestPasswordResetResponse)
async def request_password_reset(
    request: Request,
    users_logic: UsersLogicDep,
    reset_request: RequestPasswordResetRequest = Body()
):
    """
    Request a password reset email.

    Security features:
    - Rate limited (3 requests per 15 minutes per email)
    - Always returns success (prevents email enumeration)
    - Tokens expire in 30 minutes
    - Tokens are single-use
    """
    # Get client IP and user agent for audit trail
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Get frontend URL from settings (or use default for local dev)
    settings = get_settings()
    frontend_url = settings.cors_origins.split(",")[0] if settings.cors_origins else "http://localhost:3000"

    result = await users_logic.request_password_reset(
        email=reset_request.email,
        ip_address=ip_address,
        user_agent=user_agent,
        frontend_url=frontend_url
    )

    return result


@users_router.post('/reset-password', response_model=ResetPasswordResponse)
async def reset_password(
    users_logic: UsersLogicDep,
    reset_request: ResetPasswordRequest = Body()
):
    """
    Reset password using a valid token.

    Security features:
    - Token must be valid (not expired, not used)
    - Password is hashed before storing
    - Token is marked as used after successful reset
    - All other tokens for the user are invalidated
    """
    result = await users_logic.reset_password(
        token=reset_request.token,
        new_password=reset_request.new_password
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return result


@users_router.post('/change-password', response_model=ResetPasswordResponse)
async def change_password(
    users_logic: UsersLogicDep,
    change_request: ChangePasswordRequest = Body(),
    user_info: dict = Depends(get_user_info)
):
    """
    Change password for an authenticated user.

    Security features:
    - Requires authentication (JWT token)
    - Verifies current password before allowing change
    - New password must meet strength requirements
    - Password is hashed before storing
    - All password reset tokens are invalidated
    """
    result = await users_logic.change_password(
        user_id=user_info['id'],
        current_password=change_request.current_password,
        new_password=change_request.new_password
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return result


@users_router.put('/me/cookie-consent')
async def update_cookie_consent(
    request: Request,
    users_logic: UsersLogicDep,
    consent_data: CookieConsentData = Body(),
    user_info: dict = Depends(get_user_info)
):
    """
    Update cookie consent for an authenticated user.

    This endpoint tracks:
    - User's consent decision (accepted/rejected)
    - Timestamp of consent
    - IP address when consent was given
    - User agent (browser/device info) when consent was given

    Security features:
    - Requires authentication (JWT token)
    - Records audit trail for compliance
    """
    # Get client IP address and user agent for consent audit trail
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    success = await users_logic.update_cookie_consent(
        user_id=user_info['id'],
        accepted=consent_data.accepted,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cookie consent"
        )

    return {"success": True, "message": "Cookie consent updated successfully"}
