"""
Argon2id password hashing and verification module.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Configure Argon2id hasher according to RFC 9106 / OWASP recommendations
_hasher = PasswordHasher(
    time_cost=3,        # 3 iterations
    memory_cost=65536,  # 64 MiB RAM
    parallelism=4,      # 4 lanes / threads
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    if not password:
        raise ValueError("Password cannot be empty.")
    return _hasher.hash(password)


def verify_password(hash_str: str, password: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.
    Returns True if valid, False otherwise.
    """
    if not hash_str or not password:
        return False
    try:
        return _hasher.verify(hash_str, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception:
        return False


def needs_rehash(hash_str: str) -> bool:
    """Check if the hash requires updating to newer parameters."""
    try:
        return _hasher.check_needs_rehash(hash_str)
    except Exception:
        return True
