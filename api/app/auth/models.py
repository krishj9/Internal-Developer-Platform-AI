"""
Pydantic schemas and models for authentication and authorization.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=50, description="User login handle or email"
    )
    password: str = Field(..., min_length=8, description="Plaintext password")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT bearer access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Token lifetime in seconds (60 minutes)")


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    role: str
    workspaces: list[str]
    is_active: bool
    created_at: datetime | None = None


class TokenPayload(BaseModel):
    sub: str = Field(..., description="Subject / User ID")
    username: str
    email: str
    role: str
    workspaces: list[str]
    token_version: int = Field(
        default=1, description="Version of user token; increments revoke old tokens"
    )
    iss: str = Field(..., description="Issuer")
    aud: str = Field(..., description="Audience")
    iat: int = Field(..., description="Issued at epoch seconds")
    exp: int = Field(..., description="Expiration epoch seconds")
