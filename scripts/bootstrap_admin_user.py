#!/usr/bin/env python3
"""
Seed the initial platform_admin user in Firestore or print JSON seed payload.

Usage:
    python scripts/bootstrap_admin_user.py --username admin --email admin@example.com
"""

import argparse
import getpass
import json
import sys
import uuid
from datetime import datetime, timezone

from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def create_admin_payload(username: str, email: str, password: str) -> dict:
    password_hash = ph.hash(password)
    user_id = f"usr-{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "user_id": user_id,
        "username": username.lower(),
        "email": email.lower(),
        "password_hash": password_hash,
        "role": "platform_admin",
        "workspaces": ["default", "admin"],
        "token_version": 1,
        "is_active": True,
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap platform_admin user for IDP."
    )
    parser.add_argument(
        "--username", default="admin", help="Admin username (default: admin)"
    )
    parser.add_argument("--email", default="admin@example.com", help="Admin email")
    parser.add_argument(
        "--password", help="Admin password (will prompt securely if omitted)"
    )
    parser.add_argument(
        "--save-firestore",
        action="store_true",
        help="Save directly to Firestore if credentials configured",
    )
    args = parser.parse_args()

    if args.password:
        password = args.password
    else:
        password = getpass.getpass(f"Enter password for admin user '{args.username}': ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    payload = create_admin_payload(args.username, args.email, password)

    if args.save_firestore:
        from google.api_core.exceptions import GoogleAPIError
        from google.cloud import firestore

        try:
            db = firestore.Client()
            doc_ref = db.collection("users").document(payload["user_id"])
            doc_ref.set(payload)
            print(
                f"Successfully seeded admin user '{args.username}' in Firestore "
                f"(ID: {payload['user_id']})"
            )
        except GoogleAPIError as e:
            print(f"Failed to write to Firestore: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("\n--- Platform Admin Seed JSON ---")
        print(json.dumps(payload, indent=2))
        print("--------------------------------\n")


if __name__ == "__main__":
    main()
