"""Authentication API Endpoints.

User Registration, Login, Token Management.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from app.config import settings
from app.db.dynamodb import get_dynamodb_table
from app.repositories.user import UserRepository
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


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
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
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Login with email + password.

    Returns JWT access token.
    """
    # Authenticate user
    user = user_repo.authenticate(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
            joined_at=datetime.fromisoformat(org.get("joined_at", org.get("created_at")))
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
