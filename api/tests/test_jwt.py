"""
Unit tests for JWT creation, validation, expiry, and claim enforcement.
"""

from datetime import timedelta

import pytest
from api.app.auth.jwt import (
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    decode_access_token,
)
from api.app.core.settings import settings


def test_create_and_decode_token_success():
    token = create_access_token(
        user_id="usr-12345",
        username="alice",
        email="alice@example.com",
        role="developer",
        workspaces=["ws-dev"],
        token_version=1,
    )

    payload = decode_access_token(token)

    assert payload.sub == "usr-12345"
    assert payload.username == "alice"
    assert payload.email == "alice@example.com"
    assert payload.role == "developer"
    assert payload.workspaces == ["ws-dev"]
    assert payload.token_version == 1
    assert payload.iss == settings.JWT_ISSUER
    assert payload.aud == settings.JWT_AUDIENCE
    assert payload.exp - payload.iat == 3600  # Exactly 60 minutes


def test_token_expiration_rejection():
    # Create token expired 5 seconds ago
    expired_token = create_access_token(
        user_id="usr-12345",
        username="alice",
        email="alice@example.com",
        role="developer",
        workspaces=["ws-dev"],
        expires_delta=timedelta(seconds=-5),
    )

    with pytest.raises(TokenExpiredError, match="Token has expired"):
        decode_access_token(expired_token)


def test_tampered_token_rejection():
    token = create_access_token(
        user_id="usr-12345",
        username="alice",
        email="alice@example.com",
        role="developer",
        workspaces=["ws-dev"],
    )

    # Tamper with the token string
    tampered_token = token[:-5] + "XXXXX"

    with pytest.raises(TokenInvalidError):
        decode_access_token(tampered_token)


def test_wrong_secret_signature_rejection():
    token = create_access_token(
        user_id="usr-12345",
        username="alice",
        email="alice@example.com",
        role="developer",
        workspaces=["ws-dev"],
        secret_key="completely-different-signing-key-32bytes!",
    )

    with pytest.raises(TokenInvalidError):
        decode_access_token(token)  # Decodes using default settings.JWT_SECRET_KEY
