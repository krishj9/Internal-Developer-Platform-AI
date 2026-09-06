"""
Unit tests for platform repositories and concurrency locking.
"""

import pytest

from api.app.domain.models import (
    AuditEventRecord,
    CallbackEventRecord,
    DeploymentRecord,
    DeploymentStatus,
    RequestOperation,
    RequestRecord,
    RequestStatus,
    TemplateRecord,
)
from api.app.domain.state_machine import DeploymentLockedError
from api.app.repositories.platform_repositories import (
    InMemoryAuditEventRepository,
    InMemoryCallbackEventRepository,
    InMemoryDeploymentRepository,
    InMemoryRequestRepository,
    InMemoryTemplateRepository,
)


@pytest.mark.asyncio
async def test_deployment_locking_concurrency():
    repo = InMemoryDeploymentRepository()
    deployment = DeploymentRecord(
        deployment_id="dep-123",
        workspace="ws-dev",
        environment="dev",
        template_id="t1-agent-engine",
        template_version="2.0.0",
        template_commit_sha="commit-sha-1",
        owner_user_id="usr-alice",
    )
    await repo.save(deployment)

    # Request 1 acquires lock
    locked_dep = await repo.acquire_lock("dep-123", "req-001")
    assert locked_dep.active_request_id == "req-001"

    # Request 2 attempts lock -> raises DeploymentLockedError
    with pytest.raises(DeploymentLockedError, match="locked by request 'req-001'"):
        await repo.acquire_lock("dep-123", "req-002")

    # Request 1 releases lock
    await repo.release_lock("dep-123", "req-001")
    unlocked_dep = await repo.get("dep-123")
    assert unlocked_dep.active_request_id is None

    # Request 2 can now acquire lock
    await repo.acquire_lock("dep-123", "req-002")
    locked_by_req2 = await repo.get("dep-123")
    assert locked_by_req2.active_request_id == "req-002"


@pytest.mark.asyncio
async def test_request_repository_status_updates():
    repo = InMemoryRequestRepository()
    request = RequestRecord(
        request_id="req-123",
        deployment_id="dep-123",
        operation=RequestOperation.CREATE,
        status=RequestStatus.PENDING,
        workspace="ws-dev",
        environment="dev",
        template_id="t1-agent-engine",
        template_version="2.0.0",
        template_commit_sha="commit-sha-1",
        actor_user_id="usr-alice",
        actor_role="developer",
        safe_input_digest="digest-123",
    )
    await repo.save(request)

    # Valid step
    updated = await repo.update_status("req-123", RequestStatus.DISPATCHED)
    assert updated.status == RequestStatus.DISPATCHED
    assert updated.completed_at is None

    # Transition to terminal SUCCEEDED sets completed_at
    await repo.update_status("req-123", RequestStatus.PLANNING)
    await repo.update_status("req-123", RequestStatus.APPLYING)
    succeeded = await repo.update_status("req-123", RequestStatus.SUCCEEDED)
    assert succeeded.status == RequestStatus.SUCCEEDED
    assert succeeded.completed_at is not None


@pytest.mark.asyncio
async def test_callback_event_repository_append_and_ordering():
    repo = InMemoryCallbackEventRepository()

    event2 = CallbackEventRecord(
        callback_event_id="cb-2",
        request_id="req-123",
        deployment_id="dep-123",
        github_run_id="run-1",
        event_sequence=2,
        operation="create",
        status="APPLYING",
        pipeline_identity="sa-pipeline@test.iam.gserviceaccount.com",
        payload_digest="digest-2",
        safe_payload={"status": "APPLYING"},
    )
    event1 = CallbackEventRecord(
        callback_event_id="cb-1",
        request_id="req-123",
        deployment_id="dep-123",
        github_run_id="run-1",
        event_sequence=1,
        operation="create",
        status="PLANNING",
        pipeline_identity="sa-pipeline@test.iam.gserviceaccount.com",
        payload_digest="digest-1",
        safe_payload={"status": "PLANNING"},
    )

    await repo.append(event2)
    await repo.append(event1)

    events = await repo.list_by_request("req-123")
    assert len(events) == 2
    # Verify sorted by event_sequence
    assert events[0].event_sequence == 1
    assert events[1].event_sequence == 2


@pytest.mark.asyncio
async def test_audit_event_repository_append():
    repo = InMemoryAuditEventRepository()
    audit = AuditEventRecord(
        audit_event_id="aud-1",
        actor_type="user",
        actor_id="usr-alice",
        action="create_request",
        resource_type="request",
        resource_id="req-123",
        outcome="SUCCESS",
        safe_metadata={"workspace": "ws-dev"},
    )
    await repo.append(audit)

    audits = await repo.list_by_workspace("ws-dev")
    assert len(audits) == 1
    assert audits[0].actor_id == "usr-alice"


@pytest.mark.asyncio
async def test_template_repository_storage():
    repo = InMemoryTemplateRepository()
    template = TemplateRecord(
        template_id="t1-agent-engine",
        template_version="2.0.0",
        template_commit_sha="commit-sha-123",
        display_name="T1 Agent",
        description="Agent Engine",
        supported_environments=["dev"],
        allowed_models=["gemini-2.5-flash"],
        allowed_regions=["us-central1"],
        manifest={},
    )
    await repo.save(template)

    fetched = await repo.get("t1-agent-engine", "2.0.0")
    assert fetched is not None
    assert fetched.display_name == "T1 Agent"
    assert fetched.template_version == "2.0.0"
