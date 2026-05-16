"""Authentication API Endpoints.

User Registration, Login, Token Management.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.db.dynamodb import get_dynamodb_table
from app.repositories.user import UserRepository
from app.services.account_lockout import AccountLockoutService, get_account_lockout_service
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserWithOrganisationsResponse,
    TokenResponse,
    TokenPayload,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Dependencies
# ============================================================================


def get_user_repository(table=Depends(get_dynamodb_table)) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(table=table)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token.

    Args:
        data: Token payload data
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
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
    user_create: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Register new user.

    Creates user + personal organisation automatically.
    Returns JWT access token.
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

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]},
        expires_delta=access_token_expires
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
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: UserRepository = Depends(get_user_repository),
    table=Depends(get_dynamodb_table)
):
    """Login with email + password.

    Returns JWT access token.

    Security:
        - Rate limited to 10 attempts/minute per IP
        - Account locked after 5 failed attempts (15 min lockout)
        - Failed attempts reset after 30min window
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

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]},
        expires_delta=access_token_expires
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
async def logout():
    """Logout (client-side token deletion).

    JWT tokens are stateless, so logout happens client-side.
    Server could maintain blacklist if needed.
    """
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Refresh access token.

    Generates new token with extended expiry.
    """
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["id"], "email": current_user["email"]},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**current_user)
    )
