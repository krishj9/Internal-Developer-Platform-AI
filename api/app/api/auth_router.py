"""
Authentication API endpoints: Login and Me.
"""

from api.app.auth.dependencies import get_current_user
from api.app.auth.hasher import verify_password
from api.app.auth.jwt import create_access_token
from api.app.auth.models import LoginRequest, TokenResponse, UserResponse
from api.app.repositories.user_repository import UserRecord, UserRepository, user_repo
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticate with username and password to obtain a 60-minute JWT bearer token.",
)
async def login(
    req: LoginRequest,
    repository: UserRepository = Depends(lambda: user_repo),
) -> TokenResponse:
    """
    Authenticate user and issue JWT access token.
    Generic 401 response is returned on ANY authentication failure to prevent user enumeration.
    """
    generic_auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await repository.get_by_username(req.username)
    if not user:
        # Perform dummy verify to mitigate timing attacks
        verify_password(
            "$argon2id$v=19$m=65536,t=3,p=4$dGVzdHNhbHQxMjM0NTY3OA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            req.password,
        )
        raise generic_auth_error

    if not user.is_active:
        raise generic_auth_error

    if not verify_password(user.password_hash, req.password):
        raise generic_auth_error

    # Issue 60-minute JWT token
    access_token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        workspaces=user.workspaces,
        token_version=user.token_version,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,  # 60 minutes in seconds
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
    description="Retrieve the authenticated user profile. Requires a valid JWT Bearer token.",
)
async def get_me(
    current_user: UserRecord = Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        workspaces=current_user.workspaces,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
