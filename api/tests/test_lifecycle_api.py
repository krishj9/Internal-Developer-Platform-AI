"""
Integration tests for Request and Deployment lifecycle API endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from api.app.auth.hasher import hash_password
from api.app.domain.models import DeploymentStatus, RequestStatus, TemplateRecord
from api.app.main import app
from api.app.repositories.platform_repositories import deployment_repo, request_repo, template_repo
from api.app.repositories.user_repository import UserRecord, user_repo


@pytest.fixture(autouse=True)
async def seed_test_data():
    """Seed users and T1 template for integration tests."""
    alice = UserRecord(
        user_id="usr-alice",
        username="alice",
        email="alice@example.com",
        password_hash=hash_password("ValidPassword123!"),
        role="developer",
        workspaces=["ws-dev"],
        token_version=1,
        is_active=True,
    )
    admin = UserRecord(
        user_id="usr-admin",
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("AdminPass123!"),
        role="platform_admin",
        workspaces=["default", "admin", "ws-dev", "ws-prod"],
        token_version=1,
        is_active=True,
    )
    await user_repo.save(alice)
    await user_repo.save(admin)

    # Seed T1 template
    t1 = TemplateRecord(
        template_id="t1-agent-engine",
        template_version="2.0.0",
        template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
        display_name="Agent on Vertex AI Agent Engine",
        description="Governed ADK-based agent.",
        supported_environments=["dev"],
        allowed_models=["gemini-2.5-flash", "gemini-2.5-pro"],
        allowed_regions=["us-central1"],
        cost_tier="low",
        manifest={"readiness": {"type": "smoke_test"}},
        status="published",
    )
    # Seed T2 template
    t2 = TemplateRecord(
        template_id="t2-managed-rag",
        template_version="2.0.0",
        template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
        display_name="Vertex AI Managed RAG Engine",
        description="Governed Vertex AI RAG Engine stack with RagManagedDb.",
        supported_environments=["dev"],
        allowed_models=["text-embedding-004", "text-embedding-005"],
        allowed_regions=["us-central1"],
        cost_tier="medium",
        manifest={"readiness": {"type": "rag_retrieval_smoke_test"}},
        status="published",
    )
    # Seed T3 template
    t3 = TemplateRecord(
        template_id="t3-cloud-run-agent",
        template_version="2.0.0",
        template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
        display_name="Agent on Cloud Run Service",
        description="Governed ADK-based agent on Cloud Run v2.",
        supported_environments=["dev"],
        allowed_models=["gemini-2.5-flash", "gemini-2.5-pro"],
        allowed_regions=["us-central1"],
        cost_tier="medium",
        manifest={"readiness": {"type": "http_smoke_test"}},
        status="published",
    )
    await template_repo.save(t1)
    await template_repo.save(t2)
    await template_repo.save(t3)


async def get_auth_token(username: str = "alice", password: str = "ValidPassword123!") -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/auth/login", json={"username": username, "password": password})
        return res.json()["access_token"]


@pytest.mark.asyncio
async def test_list_templates():
    token = await get_auth_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/templates", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        templates = res.json()
        assert len(templates) >= 1
        assert any(t["template_id"] == "t1-agent-engine" for t in templates)


@pytest.mark.asyncio
async def test_submit_create_request_success():
    token = await get_auth_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        request_payload = {
            "workspace": "ws-dev",
            "template_id": "t1-agent-engine",
            "template_version": "2.0.0",
            "environment": "dev",
            "inputs": {
                "agent_name": "support-agent",
                "model_name": "gemini-2.5-flash",
                "region": "us-central1",
            },
        }
        res = await client.post(
            "/requests",
            json=request_payload,
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-create-001"},
        )
        assert res.status_code == 202
        data = res.json()
        assert "request_id" in data
        assert "deployment_id" in data
        assert data["status"] == "DISPATCHED"
        assert data["workspace"] == "ws-dev"


@pytest.mark.asyncio
async def test_create_request_idempotency_replay_and_mismatch():
    token = await get_auth_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "workspace": "ws-dev",
            "template_id": "t1-agent-engine",
            "environment": "dev",
            "inputs": {"agent_name": "my-agent"},
        }
        # 1. Initial submission
        res1 = await client.post(
            "/requests",
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-idemp-001"},
        )
        assert res1.status_code == 202
        req_id_1 = res1.json()["request_id"]

        # 2. Replay with identical payload -> returns cached response
        res2 = await client.post(
            "/requests",
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-idemp-001"},
        )
        assert res2.status_code == 202
        assert res2.json()["request_id"] == req_id_1

        # 3. Replay with different payload -> 409 Conflict
        payload_modified = {
            "workspace": "ws-dev",
            "template_id": "t1-agent-engine",
            "environment": "dev",
            "inputs": {"agent_name": "different-name"},
        }
        res3 = await client.post(
            "/requests",
            json=payload_modified,
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-idemp-001"},
        )
        assert res3.status_code == 409


@pytest.mark.asyncio
async def test_create_request_unauthorized_workspace_returns_403():
    token = await get_auth_token()  # Alice is in ws-dev only
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/requests",
            json={"workspace": "ws-unauthorized", "template_id": "t1-agent-engine"},
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-403"},
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_create_request_invalid_model_returns_422():
    token = await get_auth_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/requests",
            json={
                "workspace": "ws-dev",
                "template_id": "t1-agent-engine",
                "inputs": {"model_name": "unapproved-arbitrary-model"},
            },
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-422"},
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_get_deployment_and_destroy_flow():
    token = await get_auth_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create deployment
        create_res = await client.post(
            "/requests",
            json={
                "workspace": "ws-dev",
                "template_id": "t1-agent-engine",
                "inputs": {"agent_name": "destroy-target"},
            },
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-create-destroy"},
        )
        assert create_res.status_code == 202
        deployment_id = create_res.json()["deployment_id"]
        create_req_id = create_res.json()["request_id"]

        # 2. List deployments
        list_res = await client.get("/deployments", headers={"Authorization": f"Bearer {token}"})
        assert list_res.status_code == 200
        deps = list_res.json()
        assert any(d["deployment_id"] == deployment_id for d in deps)

        # 3. Get deployment config
        config_res = await client.get(
            f"/deployments/{deployment_id}/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert config_res.status_code == 200
        assert config_res.json()["deployment_id"] == deployment_id

        # 4. Attempting destroy while creation is still active -> returns 409 Conflict
        locked_destroy_res = await client.post(
            f"/deployments/{deployment_id}/destroy",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-destroy-locked"},
        )
        assert locked_destroy_res.status_code == 409

        # 5. Simulate create completion (pipeline callback sets ACTIVE and releases create lock)
        await request_repo.update_status(create_req_id, RequestStatus.PLANNING)
        await request_repo.update_status(create_req_id, RequestStatus.APPLYING)
        await request_repo.update_status(create_req_id, RequestStatus.SUCCEEDED)

        dep = await deployment_repo.get(deployment_id)
        dep.status = DeploymentStatus.ACTIVE
        await deployment_repo.save(dep)
        await deployment_repo.release_lock(deployment_id, create_req_id)

        # 6. Now submit destroy request -> 202 Accepted
        destroy_res = await client.post(
            f"/deployments/{deployment_id}/destroy",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-destroy-001"},
        )
        assert destroy_res.status_code == 202
        destroy_data = destroy_res.json()
        assert destroy_data["operation"] == "destroy"
        assert destroy_data["deployment_id"] == deployment_id
        assert destroy_data["status"] == "DISPATCHED"


@pytest.mark.asyncio
async def test_submit_t3_cloud_run_request():
    token = await get_auth_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit T3 request
        t3_payload = {
            "workspace": "ws-dev",
            "template_id": "t3-cloud-run-agent",
            "template_version": "2.0.0",
            "environment": "dev",
            "inputs": {
                "service_name": "agent-runner",
                "model_name": "gemini-2.5-flash",
                "cpu": "1",
                "memory": "512Mi",
                "max_instances": 3,
                "region": "us-central1",
            },
        }
        res = await client.post(
            "/requests",
            json=t3_payload,
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-t3-001"},
        )
        assert res.status_code == 202
        data = res.json()
        assert data["template_id"] == "t3-cloud-run-agent"
        assert data["status"] == "DISPATCHED"
        assert data["workspace"] == "ws-dev"


@pytest.mark.asyncio
async def test_submit_t2_managed_rag_request():
    token = await get_auth_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit T2 Managed RAG request
        t2_payload = {
            "workspace": "ws-dev",
            "template_id": "t2-managed-rag",
            "template_version": "2.0.0",
            "environment": "dev",
            "inputs": {
                "corpus_name": "support-knowledge",
                "embedding_model": "text-embedding-004",
                "chunk_size": 512,
                "region": "us-central1",
                "source_gcs_prefix": "gs://idp-poc-dev-docs/support",
            },
        }
        res = await client.post(
            "/requests",
            json=t2_payload,
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-t2-001"},
        )
        assert res.status_code == 202
        data = res.json()
        assert data["template_id"] == "t2-managed-rag"
        assert data["status"] == "DISPATCHED"
        assert data["workspace"] == "ws-dev"


@pytest.mark.asyncio
async def test_submit_prod_request_authorization():
    dev_token = await get_auth_token("alice", "ValidPassword123!")
    admin_token = await get_auth_token("admin", "AdminPass123!")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_payload = {
            "workspace": "ws-prod",
            "template_id": "t1-agent-engine",
            "template_version": "2.0.0",
            "environment": "prod",
            "inputs": {
                "agent_name": "prod-support-agent",
                "model_name": "gemini-2.5-pro",
                "region": "us-central1",
            },
        }

        # 1. Update t1 template to support prod environment
        t1 = await template_repo.get("t1-agent-engine", "2.0.0")
        if t1:
            t1.supported_environments = ["dev", "prod"]
            await template_repo.save(t1)

        # 2. Developer denied prod deployment -> 403 Forbidden
        denied_res = await client.post(
            "/requests",
            json=prod_payload,
            headers={
                "Authorization": f"Bearer {dev_token}",
                "Idempotency-Key": "key-prod-denied",
            },
        )
        assert denied_res.status_code == 403

        # 3. Admin allowed prod deployment -> 202 Accepted
        allowed_res = await client.post(
            "/requests",
            json=prod_payload,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Idempotency-Key": "key-prod-allowed",
            },
        )
        assert allowed_res.status_code == 202
        data = allowed_res.json()
        assert data["environment"] == "prod"
        assert data["status"] == "DISPATCHED"


@pytest.mark.asyncio
async def test_notification_service_and_slack_payload():
    from api.app.services.notification_service import NotificationEvent, notification_service

    notification_service.clear()
    event = NotificationEvent(
        event_type="PROVISIONING_SUCCEEDED",
        request_id="req-test-123",
        deployment_id="dep-test-456",
        template_id="t1-agent-engine",
        workspace="ws-dev",
        environment="dev",
        status="SUCCEEDED",
        actor_id="alice",
        summary="Agent deployed successfully",
    )
    await notification_service.publish(event)
    events = notification_service.get_published_events()
    assert len(events) == 1
    assert events[0].request_id == "req-test-123"

    slack_msg = notification_service.format_slack_message(event)
    assert "attachments" in slack_msg
    assert len(slack_msg["attachments"]) == 1
    blocks = slack_msg["attachments"][0]["blocks"]
    assert any("IDP Event: PROVISIONING_SUCCEEDED" in str(b) for b in blocks)
