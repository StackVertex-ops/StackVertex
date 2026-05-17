"""Authentication API Endpoints.

User Registration, Login, Token Management.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Header, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.db.dynamodb import get_dynamodb_table
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.services.account_lockout import AccountLockoutService, get_account_lockout_service
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserWithOrganisationsResponse,
    TokenResponse,
    TokenPayload,
)
from app.models.user import SystemRole

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_token_from_cookie_or_header(
    authorization: str | None = Header(None),
    access_token: str | None = Cookie(None)
) -> str:
    """Extract JWT token from cookie or Authorization header.

    CSRF Protection: Cookie hat Priorität (SameSite protected).
    Authorization header ist Fallback für API clients.

    Args:
        authorization: Authorization header (Bearer token)
        access_token: HttpOnly cookie

    Returns:
        JWT token

    Raises:
        HTTPException: 401 wenn kein Token gefunden
    """
    # Try cookie first (CSRF protected via SameSite)
    if access_token:
        return access_token

    # Fallback to Authorization header (für API clients)
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Dependencies
# ============================================================================


def get_user_repository(table=Depends(get_dynamodb_table)) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(table=table)


def get_refresh_token_repository(table=Depends(get_dynamodb_table)) -> RefreshTokenRepository:
    """Get RefreshTokenRepository instance."""
    return RefreshTokenRepository(table=table)


def create_access_token(data: dict) -> str:
    """Create short-lived JWT access token (15 minutes).

    Args:
        data: Token payload data

    Returns:
        Encoded JWT token
    """
    from uuid import uuid4
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,  # Issued at time
        "jti": str(uuid4()),  # Unique token ID (ensures each token is unique)
        "type": "access"  # Token type
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def create_refresh_token(data: dict) -> str:
    """Create long-lived JWT refresh token (7 days).

    Args:
        data: Token payload data

    Returns:
        Encoded JWT token
    """
    from uuid import uuid4
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": now,  # Issued at time
        "jti": str(uuid4()),  # Unique token ID (ensures each token is unique)
        "type": "refresh"  # Token type
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_refresh_token(token: str) -> dict:
    """Verify and decode refresh token.

    Args:
        token: Refresh token JWT

    Returns:
        Token payload

    Raises:
        HTTPException: If token invalid or not a refresh token
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


async def get_current_user(
    token: Annotated[str, Depends(get_token_from_cookie_or_header)],
    user_repo: UserRepository = Depends(get_user_repository)
) -> dict:
    """Get current authenticated user from JWT token.

    Args:
        token: JWT access token
        user_repo: UserRepository

    Returns:
        User dict

    Raises:
        HTTPException: If token invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from DB
    from uuid import UUID
    user = user_repo.get(UUID(user_id))

    if user is None:
        raise credentials_exception

    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_superadmin(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """Verify user is SuperAdmin.

    Args:
        current_user: Current authenticated user

    Returns:
        User dict if SuperAdmin

    Raises:
        HTTPException: 403 if not SuperAdmin
    """
    system_role = current_user.get("system_role", SystemRole.USER.value)

    if system_role != SystemRole.SUPERADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SuperAdmin access required"
        )

    return current_user


async def get_current_support(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """Verify user is Support or SuperAdmin.

    Args:
        current_user: Current authenticated user

    Returns:
        User dict if Support or SuperAdmin

    Raises:
        HTTPException: 403 if not Support or SuperAdmin
    """
    system_role = current_user.get("system_role", SystemRole.USER.value)

    if system_role not in [SystemRole.SUPERADMIN.value, SystemRole.SUPPORT.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Support access required"
        )

    return current_user


async def get_current_auditor(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """Verify user is Auditor, Support or SuperAdmin.

    Args:
        current_user: Current authenticated user

    Returns:
        User dict if Auditor, Support or SuperAdmin

    Raises:
        HTTPException: 403 if not authorized
    """
    system_role = current_user.get("system_role", SystemRole.USER.value)

    if system_role not in [
        SystemRole.SUPERADMIN.value,
        SystemRole.SUPPORT.value,
        SystemRole.AUDITOR.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auditor access required"
        )

    return current_user


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute" if settings.TESTING else "5/minute")
async def register(
    request: Request,
    response: Response,
    user_create: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository)
):
    """Register new user.

    Creates user + personal organisation automatically.
    Returns Access Token (15 min) + Refresh Token (7 days) als HttpOnly Cookies.
    """
    # Check if email already exists
    existing_user = user_repo.get_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user (includes personal org)
    user = user_repo.create(
        email=user_create.email,
        name=user_create.name,
        password=user_create.password,
        auth_provider=user_create.auth_provider,
        auth_provider_id=user_create.auth_provider_id,
    )

    logger.info(
        f"User registered: {user['id']}",
        extra={"user_id": user["id"], "email": user["email"]}
    )

    # Create Access Token (15 min)
    access_token = create_access_token({"sub": user["id"], "email": user["email"]})

    # Create Refresh Token (7 days)
    refresh_token = create_refresh_token({"sub": user["id"]})

    # Store Refresh Token in DB
    from uuid import UUID
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_repo.create(
        user_id=UUID(user["id"]),
        token=refresh_token,
        expires_at=expires_at
    )

    # Set Access Token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Set Refresh Token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**user)
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("1000/minute" if settings.TESTING else "10/minute")
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    table=Depends(get_dynamodb_table)
):
    """Login with email + password.

    Returns Access Token (15 min) + Refresh Token (7 days) als HttpOnly Cookies.

    Security:
        - Rate limited to 10 attempts/minute per IP
        - Account locked after 5 failed attempts (15 min lockout)
        - Failed attempts reset after 30min window
        - CSRF Protection via SameSite cookies
        - Token Rotation: Every refresh returns new refresh token
    """
    email = form_data.username.lower()
    ip_address = request.client.host if request.client else "unknown"

    # Create lockout service
    lockout_service = AccountLockoutService(table=table)

    # Check if account is locked
    is_locked, locked_until = lockout_service.is_account_locked(email)
    if is_locked:
        minutes_remaining = int((locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked due to too many failed login attempts. Try again in {minutes_remaining} minutes."
        )

    # Authenticate user
    user = user_repo.authenticate(email, form_data.password)

    if not user:
        # Record failed login attempt
        is_now_locked, failed_count, locked_until = lockout_service.record_failed_login(
            email, ip_address
        )

        logger.warning(
            f"Failed login attempt for {email}",
            extra={"email": email, "ip": ip_address, "failed_count": failed_count}
        )

        if is_now_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Too many failed login attempts. Account locked for {lockout_service.LOCKOUT_DURATION_MINUTES} minutes."
            )
        else:
            remaining_attempts = lockout_service.MAX_FAILED_ATTEMPTS - failed_count
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Incorrect email or password. {remaining_attempts} attempts remaining.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Successful login - clear failed attempts
    lockout_service.record_successful_login(email)

    logger.info(
        f"User logged in: {user['id']}",
        extra={"user_id": user["id"], "email": user["email"]}
    )

    # Create Access Token (15 min)
    access_token = create_access_token({"sub": user["id"], "email": user["email"]})

    # Create Refresh Token (7 days)
    refresh_token = create_refresh_token({"sub": user["id"]})

    # Store Refresh Token in DB
    from uuid import UUID
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_repo.create(
        user_id=UUID(user["id"]),
        token=refresh_token,
        expires_at=expires_at
    )

    # Set Access Token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Set Refresh Token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**user)
    )


@router.get("/me", response_model=UserWithOrganisationsResponse)
async def get_current_user_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get current authenticated user profile mit organisations."""
    from uuid import UUID

    # Get user's organisations
    orgs = user_repo.get_organisations(UUID(current_user["id"]))

    # Build response
    from app.schemas.user import UserMembershipResponse

    memberships = [
        UserMembershipResponse(
            organisation_id=UUID(org["org_id"]),
            organisation_name=org["org_name"],
            role=org["role"],
            joined_at=datetime.fromisoformat(org["joined_at"]) if "joined_at" in org else datetime.utcnow()
        )
        for org in orgs
    ]

    user_response = UserWithOrganisationsResponse(
        **current_user,
        organisations=memberships
    )

    return user_response


@router.post("/logout")
async def logout(
    response: Response,
    current_user: Annotated[dict, Depends(get_current_user)],
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository)
):
    """Logout - revokes all refresh tokens and clears cookies.

    Invalidiert alle Refresh Tokens des Users (logout from all devices).
    Löscht Access + Refresh Token Cookies.
    """
    # Revoke all refresh tokens for user
    from uuid import UUID
    refresh_token_repo.revoke_all_for_user(UUID(current_user["id"]))

    # Clear cookies
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(None),
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository)
):
    """Refresh Access Token using Refresh Token.

    Returns new Access Token + new Refresh Token (Token Rotation).

    Security:
        - Validates Refresh Token from cookie
        - Checks token exists in DB and is not revoked
        - Revokes old Refresh Token (prevents replay attacks)
        - Issues new Access + Refresh Token pair
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    # Verify Refresh Token JWT
    try:
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("sub")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check if token exists in DB and is valid
    token_item = refresh_token_repo.get_by_token(refresh_token)
    if not token_item:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or expired"
        )

    # Get user
    from uuid import UUID
    user = user_repo.get(UUID(user_id))
    if not user or user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # REVOKE old Refresh Token (Token Rotation)
    refresh_token_repo.revoke(token_item["id"], UUID(user_id))

    logger.info(
        f"Token refreshed for user: {user_id}",
        extra={"user_id": user_id, "ip": request.client.host if request.client else "unknown"}
    )

    # Create NEW Access Token (15 min)
    new_access_token = create_access_token({"sub": user_id, "email": user["email"]})

    # Create NEW Refresh Token (7 days)
    new_refresh_token = create_refresh_token({"sub": user_id})

    # Store new Refresh Token
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_repo.create(
        user_id=UUID(user_id),
        token=new_refresh_token,
        expires_at=expires_at
    )

    # Set new Access Token cookie
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Set new Refresh Token cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**user)
    )
