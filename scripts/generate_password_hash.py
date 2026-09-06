#!/usr/bin/env python3
"""
Generate an Argon2id password hash for user seeding in the IDP Control Plane.

Usage:
    python scripts/generate_password_hash.py
    python scripts/generate_password_hash.py --password "MySecretPass123!"
"""

import argparse
import getpass
import sys

from argon2 import PasswordHasher
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

# Recommended Argon2id parameters (RFC 9106 / OWASP standard)
ph = PasswordHasher(
    time_cost=3,  # Iterations
    memory_cost=65536,  # 64 MiB
    parallelism=4,  # 4 threads
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    if not password:
        raise ValueError("Password cannot be empty.")
    return ph.hash(password)


def verify_password(hash_str: str, password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return ph.verify(hash_str, password)
    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
        ValueError,
        TypeError,
    ):
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate Argon2id password hash for IDP users.")
    parser.add_argument(
        "--password",
        "-p",
        help="Password to hash. If omitted, you will be prompted securely.",
        default=None,
    )
    args = parser.parse_args()

    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter password to hash: ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    try:
        hashed = hash_password(password)
        print("\n--- Argon2id Password Hash ---")
        print(hashed)
        print("------------------------------\n")
    except HashingError as e:
        print(f"Error hashing password: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
