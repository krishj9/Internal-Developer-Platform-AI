#!/usr/bin/env python3
"""
Clean up IDP Control Plane Firestore Database for a Fresh Start.

This script deletes operational lifecycle records (deployments, requests, callbacks,
audit logs, and idempotency records) from the Firestore database. It can optionally
purge or re-seed baseline user accounts and published template catalog records.

Usage:
    # Safe cleanup of operational records only (prompts for confirmation)
    python scripts/cleanup_database.py

    # Non-interactive cleanup with dry-run inspection
    python scripts/cleanup_database.py --dry-run

    # Complete wipe and fresh re-seed of baseline users and templates
    python scripts/cleanup_database.py --all --reseed --yes

    # Target specific GCP project and database
    python scripts/cleanup_database.py --project mybrightday-dev --database idp-db --yes

    # Clean up via running Control Plane API (works for both in-memory and Firestore)
    python scripts/cleanup_database.py --api-url http://127.0.0.1:8000 --yes
"""

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

from argon2 import PasswordHasher

# Standard Argon2id hasher matching API hasher configuration
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

OPERATIONAL_COLLECTIONS = [
    "deployments",
    "requests",
    "callback_events",
    "audit_events",
    "idempotency_records",
]

BASELINE_COLLECTIONS = [
    "users",
    "templates",
]

DEFAULT_USERS = [
    {
        "user_id": "usr-admin-gov",
        "username": "admin_gov",
        "email": "admin_gov@mybrightday-dev.internal",
        "password": "RY%%H4uIjQFAfQ15!=2l2z",
        "role": "platform_admin",
        "workspaces": ["default", "admin", "ws-dev"],
        "token_version": 2,
        "is_active": True,
    },
    {
        "user_id": "usr-dev-gov",
        "username": "dev_gov",
        "email": "dev_gov@mybrightday-dev.internal",
        "password": "oZ!f83h1vxp0v$rJAM#!H8",
        "role": "developer",
        "workspaces": ["default", "ws-dev"],
        "token_version": 2,
        "is_active": True,
    },
    {
        "user_id": "usr-admin-default",
        "username": "admin",
        "email": "admin@mybrightday-dev.internal",
        "password": "KotC-vurzwtBKgP7#x%5r+",
        "role": "platform_admin",
        "workspaces": ["default", "admin"],
        "token_version": 2,
        "is_active": True,
    },
]

DEFAULT_TEMPLATES = [
    {
        "template_id": "t1-agent-engine",
        "template_version": "2.0.0",
        "template_commit_sha": "010078cf6745f44da605f6fa0768b4f177c385a5",
        "display_name": "Agent on Vertex AI Agent Engine",
        "description": "Governed ADK-based agent deployed to Google Cloud Agent Engine.",
        "supported_environments": ["dev"],
        "allowed_models": ["gemini-2.5-flash", "gemini-2.5-pro"],
        "allowed_regions": ["us-central1"],
        "cost_tier": "low",
        "manifest": {"readiness": {"type": "smoke_test"}},
        "status": "published",
    },
    {
        "template_id": "t2-managed-rag",
        "template_version": "2.0.0",
        "template_commit_sha": "010078cf6745f44da605f6fa0768b4f177c385a5",
        "display_name": "Vertex AI Managed RAG Engine",
        "description": "Governed Vertex AI RAG Engine stack with RagManagedDb.",
        "supported_environments": ["dev"],
        "allowed_models": ["text-embedding-004", "text-embedding-005"],
        "allowed_regions": ["us-central1"],
        "cost_tier": "medium",
        "manifest": {"readiness": {"type": "rag_retrieval_smoke_test"}},
        "status": "published",
    },
    {
        "template_id": "t3-cloud-run-agent",
        "template_version": "2.0.0",
        "template_commit_sha": "010078cf6745f44da605f6fa0768b4f177c385a5",
        "display_name": "Agent on Cloud Run Service",
        "description": "Governed ADK-based agent deployed to Google Cloud Run v2.",
        "supported_environments": ["dev"],
        "allowed_models": ["gemini-2.5-flash", "gemini-2.5-pro"],
        "allowed_regions": ["us-central1"],
        "cost_tier": "medium",
        "manifest": {"readiness": {"type": "http_smoke_test"}},
        "status": "published",
    },
    {
        "template_id": "t4-governance",
        "template_version": "2.0.0",
        "template_commit_sha": "010078cf6745f44da605f6fa0768b4f177c385a5",
        "display_name": "Governance & Operational Controls",
        "description": (
            "Governed Model Armor guardrails, Cloud Monitoring alerts, "
            "and automated TTL policies."
        ),
        "supported_environments": ["dev", "prod"],
        "allowed_models": [],
        "allowed_regions": ["us-central1"],
        "cost_tier": "low",
        "manifest": {"readiness": {"type": "policy_verification_test"}},
        "status": "published",
    },
]


def get_firestore_client(project_id: str, database: str) -> Any:
    """
    Initialize a Google Cloud Firestore Client with credentials fallback.
    """
    from google.cloud import firestore
    from google.oauth2 import credentials

    # Support local Firestore emulator
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        return firestore.Client(project=project_id, database=database)

    try:
        return firestore.Client(project=project_id, database=database)
    except Exception:
        # Fallback to gcloud access token if ADC environment is unconfigured
        try:
            token = subprocess.check_output(
                ["gcloud", "auth", "print-access-token"], text=True
            ).strip()
            creds = credentials.Credentials(token)
            return firestore.Client(project=project_id, database=database, credentials=creds)
        except Exception as e:
            print(
                f"\n❌ Error: Unable to authenticate with Google Cloud Firestore: {e}\n\n"
                "To authenticate with Google Cloud, please run:\n"
                "    gcloud auth application-default login\n"
                "  or:\n"
                "    gcloud auth login\n\n"
                "If you are running the local control plane dev server, run:\n"
                "    python scripts/cleanup_database.py --api-url http://127.0.0.1:8000 --yes\n\n"
                "If using a local Firestore emulator, configure:\n"
                "    export FIRESTORE_EMULATOR_HOST=localhost:8080\n",
                file=sys.stderr,
            )
            sys.exit(1)


def count_documents(db: Any, collection_name: str) -> int:
    """Return the total number of documents in a collection."""
    coll_ref = db.collection(collection_name)
    docs = list(coll_ref.stream())
    return len(docs)


def delete_collection(db: Any, collection_name: str, batch_size: int = 450) -> int:
    """
    Delete all documents from a collection in batches.
    Returns the total number of documents deleted.
    """
    coll_ref = db.collection(collection_name)
    total_deleted = 0

    while True:
        docs = list(coll_ref.limit(batch_size).stream())
        if not docs:
            break

        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()
        total_deleted += len(docs)

    return total_deleted


def reseed_baseline_users(db: Any) -> int:
    """Reseed default platform admin and developer users."""
    users_coll = db.collection("users")
    now_iso = datetime.now(UTC).isoformat()
    seeded = 0

    for u in DEFAULT_USERS:
        doc_ref = users_coll.document(u["user_id"])
        payload = {
            "user_id": u["user_id"],
            "username": u["username"],
            "email": u["email"],
            "password_hash": ph.hash(u["password"]),
            "role": u["role"],
            "workspaces": u["workspaces"],
            "token_version": u["token_version"],
            "is_active": u["is_active"],
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        doc_ref.set(payload)
        seeded += 1

    return seeded


def reseed_baseline_templates(db: Any) -> int:
    """Reseed published immutable template records."""
    templates_coll = db.collection("templates")
    seeded = 0

    for t in DEFAULT_TEMPLATES:
        doc_id = f"{t['template_id']}@{t['template_version']}"
        doc_ref = templates_coll.document(doc_id)
        doc_ref.set(t)
        seeded += 1

    return seeded


def cleanup_via_api(
    api_url: str,
    username: str,
    password: str,
    include_users: bool,
    include_templates: bool,
    reseed: bool,
) -> None:
    """Execute cleanup via the IDP Control Plane API."""
    import httpx

    base_url = api_url.rstrip("/")
    print(f"Connecting to IDP API at {base_url}...")

    try:
        # Authenticate as admin
        login_resp = httpx.post(
            f"{base_url}/auth/login",
            json={"username": username, "password": password},
            timeout=10.0,
        )
        if login_resp.status_code != 200:
            print(
                f"Error: API authentication failed ({login_resp.status_code}): {login_resp.text}",
                file=sys.stderr,
            )
            sys.exit(1)

        token = login_resp.json().get("access_token")

        # Invoke cleanup endpoint
        clean_resp = httpx.post(
            f"{base_url}/admin/cleanup-database",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "include_users": include_users,
                "include_templates": include_templates,
                "reseed": reseed,
            },
            timeout=30.0,
        )
        if clean_resp.status_code != 200:
            print(
                f"Error: API cleanup request failed ({clean_resp.status_code}): {clean_resp.text}",
                file=sys.stderr,
            )
            sys.exit(1)

        data = clean_resp.json()
        print("\n" + "=" * 65)
        print("✅ DATABASE CLEANUP COMPLETED SUCCESSFULLY VIA API")
        print("=" * 65)
        print(f"  • Purged Collections: {', '.join(data.get('purged_collections', []))}")
        print(f"  • Reseeded Users:     {data.get('reseeded_users', 0)}")
        print(f"  • Reseeded Templates: {data.get('reseeded_templates', 0)}")
        print(f"  • Message:            {data.get('message', '')}")
        print("=" * 65 + "\n")

    except httpx.ConnectError:
        print(f"Error: Could not connect to API server at {base_url}.", file=sys.stderr)
        print("Ensure the API server is running or omit --api-url for direct Firestore cleanup.")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean up IDP Firestore database collections for a fresh start."
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GCP_PROJECT") or os.getenv("PROJECT_ID") or "mybrightday-dev",
        help="Google Cloud Project ID (default: mybrightday-dev)",
    )
    parser.add_argument(
        "--database",
        default=os.getenv("FIRESTORE_DATABASE", "idp-db"),
        help="Firestore database ID (default: idp-db)",
    )
    parser.add_argument(
        "--api-url",
        help="Target IDP Control Plane API URL (e.g. http://127.0.0.1:8000). Cleans active state.",
    )
    parser.add_argument(
        "--admin-username",
        default="admin_gov",
        help="Admin username for API cleanup (default: admin_gov)",
    )
    parser.add_argument(
        "--admin-password",
        default="RY%%H4uIjQFAfQ15!=2l2z",
        help="Admin password for API cleanup",
    )
    parser.add_argument(
        "--collections",
        help="Comma-separated list of specific collections to purge (e.g. deployments,requests)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Purge ALL collections, including users and templates",
    )
    parser.add_argument(
        "--include-users",
        action="store_true",
        help="Include 'users' collection in the cleanup",
    )
    parser.add_argument(
        "--include-templates",
        action="store_true",
        help="Include 'templates' collection in the cleanup",
    )
    parser.add_argument(
        "--reseed",
        action="store_true",
        help="Automatically reseed baseline users and published templates after cleanup",
    )
    parser.add_argument(
        "--reseed-users",
        action="store_true",
        help="Reseed baseline users after cleanup",
    )
    parser.add_argument(
        "--reseed-templates",
        action="store_true",
        help="Reseed baseline published templates after cleanup",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect collections and report document counts without performing deletions",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip interactive confirmation prompt",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # If --api-url is provided, route cleanup through the API
    if args.api_url:
        include_users = args.all or args.include_users
        include_templates = args.all or args.include_templates
        reseed = args.reseed or args.reseed_users or args.reseed_templates or True

        if not args.yes:
            prompt_msg = (
                f"⚠️  WARNING: This will clean up database state via {args.api_url}.\n"
                "Proceed? [y/N]: "
            )
            confirm = input(prompt_msg)
            if confirm.strip().lower() not in ("y", "yes"):
                print("Operation aborted by user.")
                sys.exit(0)

        cleanup_via_api(
            api_url=args.api_url,
            username=args.admin_username,
            password=args.admin_password,
            include_users=include_users,
            include_templates=include_templates,
            reseed=reseed,
        )
        return

    # Determine target collections for direct Firestore cleanup
    if args.collections:
        target_collections = [c.strip() for c in args.collections.split(",") if c.strip()]
    elif args.all:
        target_collections = OPERATIONAL_COLLECTIONS + BASELINE_COLLECTIONS
    else:
        target_collections = list(OPERATIONAL_COLLECTIONS)
        if args.include_users and "users" not in target_collections:
            target_collections.append("users")
        if args.include_templates and "templates" not in target_collections:
            target_collections.append("templates")

    print("\n" + "=" * 65)
    print("🧹 IDP FIRESTORE DATABASE CLEANUP")
    print("=" * 65)
    print(f"  • GCP Project:        {args.project}")
    print(f"  • Database:           {args.database}")
    print(f"  • Mode:               {'DRY RUN (Simulated)' if args.dry_run else 'LIVE PURGE'}")
    print(f"  • Target Collections: {', '.join(target_collections)}")
    if args.reseed or args.reseed_users or args.reseed_templates:
        reseed_items = []
        if args.reseed or args.reseed_users:
            reseed_items.append("Users (admin_gov, dev_gov, admin)")
        if args.reseed or args.reseed_templates:
            reseed_items.append("Templates (t1, t2, t3, t4)")
        print(f"  • Reseed Target:      {', '.join(reseed_items)}")
    print("=" * 65 + "\n")

    # Connect to Firestore
    db = get_firestore_client(args.project, args.database)

    # Inspect current document counts
    print("Inspecting collection document counts...")
    counts: dict[str, int] = {}
    for coll in target_collections:
        try:
            cnt = count_documents(db, coll)
            counts[coll] = cnt
            print(f"  - {coll:<22}: {cnt} documents found")
        except Exception as e:
            print(f"  - {coll:<22}: Error reading collection ({e})")
            counts[coll] = 0

    total_docs = sum(counts.values())
    print(f"\nTotal documents targeted for deletion: {total_docs}\n")

    if args.dry_run:
        print("🔍 DRY RUN COMPLETE: No documents were deleted.")
        return

    if total_docs == 0 and not (args.reseed or args.reseed_users or args.reseed_templates):
        print("Database is already clean. Nothing to do.")
        return

    # Confirmation prompt
    if not args.yes:
        confirm = input(
            f"⚠️  WARNING: Deletion is permanent! Proceed with cleaning {args.database}? [y/N]: "
        )
        if confirm.strip().lower() not in ("y", "yes"):
            print("Operation aborted by user.")
            sys.exit(0)

    # Perform deletions
    print("\nPurging collections...")
    for coll in target_collections:
        if counts.get(coll, 0) == 0:
            print(f"  • {coll:<22}: Skipped (0 documents)")
            continue

        deleted = delete_collection(db, coll)
        print(f"  • {coll:<22}: Deleted {deleted} documents")

    # Reseed baseline data if requested
    if args.reseed or args.reseed_users:
        print("\nReseeding baseline users...")
        users_count = reseed_baseline_users(db)
        print(f"  • Reseeded {users_count} baseline users (admin_gov, dev_gov, admin).")

    if args.reseed or args.reseed_templates:
        print("\nReseeding baseline templates...")
        tpl_count = reseed_baseline_templates(db)
        print(f"  • Reseeded {tpl_count} published templates (t1, t2, t3, t4).")

    print("\n" + "=" * 65)
    print("✅ DATABASE CLEANUP COMPLETED SUCCESSFULLY")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
