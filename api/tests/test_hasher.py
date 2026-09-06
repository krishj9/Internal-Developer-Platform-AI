"""
Unit tests for Argon2id password hashing and verification.
"""

import pytest

from api.app.auth.hasher import hash_password, needs_rehash, verify_password


def test_hash_and_verify_password_success():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, password) is True


def test_verify_password_mismatch_returns_false():
    password = "CorrectPassword123!"
    hashed = hash_password(password)

    assert verify_password(hashed, "WrongPassword!") is False
    assert verify_password(hashed, "") is False
    assert verify_password("", password) is False


def test_empty_password_raises_value_error():
    with pytest.raises(ValueError, match="Password cannot be empty"):
        hash_password("")


def test_needs_rehash_on_fresh_hash():
    password = "AnotherPassword456!"
    hashed = hash_password(password)

    # Freshly generated hash using current parameters should not need rehash
    assert needs_rehash(hashed) is False
