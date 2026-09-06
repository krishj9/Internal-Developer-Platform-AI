"""
Unit tests for the Idempotency service, hashing, and 24-hour TTL mechanics.
"""

from datetime import UTC, datetime, timedelta
import pytest

from api.app.domain.models import IdempotencyRecord
from api.app.repositories.platform_repositories import InMemoryIdempotencyRepository
from api.app.services.idempotency_service import (
    IdempotencyMismatchError,
    IdempotencyService,
    compute_payload_digest,
)


def test_compute_payload_digest_determinism():
    payload_a = {"template_id": "t1-agent-engine", "inputs": {"model": "gemini-2.5-flash", "region": "us-central1"}}
    payload_b = {"inputs": {"region": "us-central1", "model": "gemini-2.5-flash"}, "template_id": "t1-agent-engine"}

    # Keys ordered differently must produce identical digests
    digest_a = compute_payload_digest(payload_a)
    digest_b = compute_payload_digest(payload_b)
    assert digest_a == digest_b

    # Modified payload must produce different digest
    payload_c = {"template_id": "t1-agent-engine", "inputs": {"model": "gemini-2.5-pro", "region": "us-central1"}}
    digest_c = compute_payload_digest(payload_c)
    assert digest_a != digest_c


@pytest.mark.asyncio
async def test_idempotency_first_request_and_replay():
    repo = InMemoryIdempotencyRepository()
    service = IdempotencyService(repository=repo)

    payload = {"template_id": "t1-agent-engine", "inputs": {"agent_name": "agent-1"}}

    # 1. First time request returns None
    result = await service.check_idempotency("usr-alice", "key-12345", payload)
    assert result is None

    # 2. Record response
    await service.record_response(
        user_id="usr-alice",
        idempotency_key="key-12345",
        payload=payload,
        status_code=202,
        response_body={"request_id": "req-100", "status": "PENDING"},
    )

    # 3. Replay with identical payload returns previous result
    cached_result = await service.check_idempotency("usr-alice", "key-12345", payload)
    assert cached_result is not None
    status_code, body = cached_result
    assert status_code == 202
    assert body["request_id"] == "req-100"


@pytest.mark.asyncio
async def test_idempotency_mismatched_payload_raises_error():
    repo = InMemoryIdempotencyRepository()
    service = IdempotencyService(repository=repo)

    payload_1 = {"template_id": "t1-agent-engine", "inputs": {"agent_name": "agent-1"}}
    payload_2 = {"template_id": "t1-agent-engine", "inputs": {"agent_name": "different-name"}}

    # Record response for payload 1
    await service.record_response(
        user_id="usr-alice",
        idempotency_key="key-12345",
        payload=payload_1,
        status_code=202,
        response_body={"request_id": "req-100"},
    )

    # Replaying same key with payload 2 raises IdempotencyMismatchError
    with pytest.raises(IdempotencyMismatchError, match="reused with different payload"):
        await service.check_idempotency("usr-alice", "key-12345", payload_2)


@pytest.mark.asyncio
async def test_idempotency_ttl_expiration():
    repo = InMemoryIdempotencyRepository()
    service = IdempotencyService(repository=repo)

    payload = {"template_id": "t1-agent-engine"}
    digest = compute_payload_digest(payload)

    # Manually insert an expired record (expired 1 hour ago)
    expired_record = IdempotencyRecord(
        idempotency_key="key-expired",
        user_id="usr-alice",
        payload_digest=digest,
        status_code=202,
        response_body={"request_id": "req-old"},
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    await repo.save(expired_record)

    # Expired record should be treated as non-existent
    result = await service.check_idempotency("usr-alice", "key-expired", payload)
    assert result is None
