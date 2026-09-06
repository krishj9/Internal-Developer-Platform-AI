"""
Idempotency service for create and destroy lifecycle operations.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from api.app.domain.models import IdempotencyRecord
from api.app.repositories.platform_repositories import IdempotencyRepository, idempotency_repo


class IdempotencyMismatchError(Exception):
    """Raised when an existing idempotency key is reused with a different payload."""
    pass


def compute_payload_digest(payload: dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 digest of a JSON-serializable dictionary.
    """
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class IdempotencyService:
    def __init__(self, repository: IdempotencyRepository = idempotency_repo):
        self._repo = repository

    async def check_idempotency(
        self, user_id: str, idempotency_key: str, payload: dict[str, Any]
    ) -> tuple[int, dict[str, Any]] | None:
        """
        Check if an idempotency record exists for the given user and key.
        Returns (status_code, response_body) if an exact match exists.
        Raises IdempotencyMismatchError if key exists but payload digest differs.
        Returns None if no previous record exists.
        """
        if not idempotency_key:
            return None

        current_digest = compute_payload_digest(payload)
        record = await self._repo.get(user_id, idempotency_key)

        if not record:
            return None

        if record.payload_digest != current_digest:
            raise IdempotencyMismatchError(
                f"Idempotency key '{idempotency_key}' was reused with different payload."
            )

        return record.status_code, record.response_body

    async def record_response(
        self,
        user_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
        status_code: int,
        response_body: dict[str, Any],
        ttl_hours: int = 24,
    ) -> None:
        """
        Store the idempotency outcome with a 24-hour expiration TTL.
        """
        if not idempotency_key:
            return

        digest = compute_payload_digest(payload)
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=ttl_hours)

        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            user_id=user_id,
            payload_digest=digest,
            status_code=status_code,
            response_body=response_body,
            expires_at=expires_at,
            created_at=now,
        )
        await self._repo.save(record)


idempotency_service = IdempotencyService()
