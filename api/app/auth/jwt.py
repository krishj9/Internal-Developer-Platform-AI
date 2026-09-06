"""
JWT creation, decoding, and validation primitives.
"""

from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    PyJWTError,
)

from api.app.auth.models import TokenPayload
from api.app.core.settings import settings


class JWTValidationError(Exception):
    """Base exception for JWT validation failures."""

    pass


class TokenExpiredError(JWTValidationError):
    """Token has passed its expiration time."""

    pass


class TokenInvalidError(JWTValidationError):
    """Token signature, issuer, audience, or structure is invalid."""

    pass


def create_access_token(
    user_id: str,
    username: str,
    email: str,
    role: str,
    workspaces: list[str],
    token_version: int = 1,
    expires_delta: timedelta | None = None,
    secret_key: str | None = None,
) -> str:
    """
    Generate a signed 60-minute JWT bearer token.
    """
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "role": role,
        "workspaces": workspaces,
        "token_version": token_version,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    key = secret_key or settings.JWT_SECRET_KEY
    return jwt.encode(payload, key, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(
    token: str,
    secret_key: str | None = None,
) -> TokenPayload:
    """
    Decode and validate a JWT access token against algorithm, issuer, audience, and expiry.
    """
    if not token:
        raise TokenInvalidError("Token is missing or empty.")

    key = secret_key or settings.JWT_SECRET_KEY

    required_claims = [
        "sub",
        "username",
        "email",
        "role",
        "workspaces",
        "token_version",
        "exp",
        "iat",
        "iss",
        "aud",
    ]

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "verify_aud": True,
                "require": required_claims,
            },
        )
        return TokenPayload(**payload)
    except ExpiredSignatureError as e:
        raise TokenExpiredError("Token has expired.") from e
    except (InvalidSignatureError, InvalidIssuerError, InvalidAudienceError, DecodeError) as e:
        raise TokenInvalidError(f"Invalid token: {e!s}") from e
    except PyJWTError as e:
        raise TokenInvalidError(f"Token decoding error: {e!s}") from e
    except Exception as e:
        raise TokenInvalidError(f"Malformed token payload: {e!s}") from e
