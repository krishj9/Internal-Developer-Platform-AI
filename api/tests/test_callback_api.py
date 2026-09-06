"""
Positive and negative integration tests for Pipeline Callbacks and Admin Reconciliation.
"""

import pytest
from api.app.auth.hasher import hash_password
from api.app.domain.models import DeploymentStatus, TemplateRecord
from api.app.main import app
from api.app.repositories.platform_repositories import deployment_repo, template_repo
from api.app.repositories.user_repository import UserRecord, user_repo
from httpx import ASGITransport, AsyncClient

PIPELINE_TOKEN = "test-pipeline-token-valid-id-token"


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

    t1 = TemplateRecord(
        template_id="t1-agent-engine",
        template_version="2.0.0",
        template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
        display_name="Agent on Vertex AI Agent Engine",
        description="Governed ADK-based agent.",
        supported_environments=["dev"],
        allowed_models=["gemini-2.5-flash"],
        allowed_regions=["us-central1"],
        cost_tier="low",
        manifest={"readiness": {"type": "smoke_test"}},
        status="published",
    )
    await template_repo.save(t1)


async def get_user_token(username: str = "alice", password: str = "ValidPassword123!") -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/auth/login", json={"username": username, "password": password})
        return res.json()["access_token"]


@pytest.mark.asyncio
async def test_full_create_callback_progression():
    user_token = await get_user_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Submit create request
        create_res = await client.post(
            "/requests",
            json={"workspace": "ws-dev", "template_id": "t1-agent-engine"},
            headers={"Authorization": f"Bearer {user_token}", "Idempotency-Key": "key-cb-flow"},
        )
        assert create_res.status_code == 202
        req_data = create_res.json()
        req_id = req_data["request_id"]
        dep_id = req_data["deployment_id"]

        # Base payload for callbacks
        base_cb = {
            "request_id": req_id,
            "deployment_id": dep_id,
            "template_id": "t1-agent-engine",
            "template_version": "2.0.0",
            "template_commit_sha": "010078cf6745f44da605f6fa0768b4f177c385a5",
            "repository": "idp-platform-org/idp-platform",
            "workflow": "deploy-t1.yml",
            "github_run_id": "999888111",
            "operation": "create",
        }

        # 2. PLANNING Callback (Seq 1)
        cb1 = await client.post(
            "/callbacks/pipeline",
            json={**base_cb, "event_sequence": 1, "status": "PLANNING", "summary": "Plan started"},
            headers={"Authorization": f"Bearer {PIPELINE_TOKEN}"},
        )
        assert cb1.status_code == 200
        assert cb1.json()["request_status"] == "PLANNING"

        # 3. APPLYING Callback (Seq 2)
        cb2 = await client.post(
            "/callbacks/pipeline",
            json={**base_cb, "event_sequence": 2, "status": "APPLYING", "summary": "Apply started"},
            headers={"Authorization": f"Bearer {PIPELINE_TOKEN}"},
        )
        assert cb2.status_code == 200
        assert cb2.json()["request_status"] == "APPLYING"

        # Check deployment moved to PROVISIONING
        dep = await deployment_repo.get(dep_id)
        assert dep.status == DeploymentStatus.PROVISIONING

        # 4. VALIDATING Callback (Seq 3)
        cb3 = await client.post(
            "/callbacks/pipeline",
            json={
                **base_cb,
                "event_sequence": 3,
                "status": "VALIDATING",
                "summary": "Readiness smoke test",
            },
            headers={"Authorization": f"Bearer {PIPELINE_TOKEN}"},
        )
        assert cb3.status_code == 200

        # 5. SUCCEEDED Callback (Seq 4)
        cb4 = await client.post(
            "/callbacks/pipeline",
            json={
                **base_cb,
                "event_sequence": 4,
                "status": "SUCCEEDED",
                "summary": "Deployment active",
                "outputs": {
                    "agent_endpoint": "projects/123/locations/us-central1/reasoningEngines/456"
                },
            },
            headers={"Authorization": f"Bearer {PIPELINE_TOKEN}"},
        )
        assert cb4.status_code == 200
        assert cb4.json()["request_status"] == "SUCCEEDED"

        # Check deployment moved to ACTIVE, lock released, outputs saved
        final_dep = await deployment_repo.get(dep_id)
        assert final_dep.status == DeploymentStatus.ACTIVE
        assert final_dep.active_request_id is None
        assert "agent_endpoint" in final_dep.safe_outputs


@pytest.mark.asyncio
async def test_callback_rejection_on_user_jwt_token():
    user_token = await get_user_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to call pipeline callback endpoint using a human user JWT
        res = await client.post(
            "/callbacks/pipeline",
            json={"request_id": "req-fake", "deployment_id": "dep-fake"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert res.status_code == 403
        assert "User portal JWTs cannot authenticate" in res.json()["detail"]


@pytest.mark.asyncio
async def test_callback_binding_mismatch_rejection():
    user_token = await get_user_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create valid request
        create_res = await client.post(
            "/requests",
            json={"workspace": "ws-dev", "template_id": "t1-agent-engine"},
            headers={"Authorization": f"Bearer {user_token}", "Idempotency-Key": "key-cb-bind"},
        )
        req_data = create_res.json()

        # Send callback with wrong deployment_id
        cb_payload = {
            "request_id": req_data["request_id"],
            "deployment_id": "dep-WRONG-ID",
            "template_id": "t1-agent-engine",
            "template_version": "2.0.0",
            "template_commit_sha": "010078cf6745f44da605f6fa0768b4f177c385a5",
            "repository": "idp-platform-org/idp-platform",
            "workflow": "deploy-t1.yml",
            "github_run_id": "999888111",
            "event_sequence": 1,
            "operation": "create",
            "status": "PLANNING",
            "summary": "Plan started",
        }
        res = await client.post(
            "/callbacks/pipeline",
            json=cb_payload,
            headers={"Authorization": f"Bearer {PIPELINE_TOKEN}"},
        )
        assert res.status_code == 422
        assert "Deployment ID does not match" in res.json()["detail"]


@pytest.mark.asyncio
async def test_callback_duplicate_and_stale_sequence():
    user_token = await get_user_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/requests",
            json={"workspace": "ws-dev", "template_id": "t1-agent-engine"},
            headers={"Authorization": f"Bearer {user_token}", "Idempotency-Key": "key-cb-seq"},
        )
        req_data = create_res.json()
        base_cb = {
            "request_id": req_data["request_id"],
            "deployment_id": req_data["deployment_id"],
            "template_id": "t1-agent-engine",
            "template_version": "2.0.0",
            "template_commit_sha": "010078cf6745f44da605f6fa0768b4f177c385a5",
            "repository": "idp-platform-org/idp-platform",
            "workflow": "deploy-t1.yml",
            "github_run_id": "999888111",
            "operation": "create",
            "status": "PLANNING",
            "summary": "Plan started",
        }

        # 1. Send seq 1
        res1 = await client.post(
            "/callbacks/pipeline",
            json={**base_cb, "event_sequence": 1},
            headers={"Authorization": f"Bearer {PIPELINE_TOKEN}"},
        )
        assert res1.status_code == 200

        # 2. Resend exact seq 1 (Duplicate -> returns 200 accepted idempotently)
        res_dup = await client.post(
            "/callbacks/pipeline",
            json={**base_cb, "event_sequence": 1},
            headers={"Authorization": f"Bearer {PIPELINE_TOKEN}"},
        )
        assert res_dup.status_code == 200

        # 3. Send stale sequence (seq 1 with conflicting status APPLYING -> 409 Conflict)
        res_stale = await client.post(
            "/callbacks/pipeline",
            json={**base_cb, "event_sequence": 1, "status": "APPLYING"},
            headers={"Authorization": f"Bearer {PIPELINE_TOKEN}"},
        )
        assert res_stale.status_code == 409


@pytest.mark.asyncio
async def test_admin_reconciliation_endpoint():
    user_token = await get_user_token("alice")
    admin_token = await get_user_token("admin", "AdminPass123!")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create request
        create_res = await client.post(
            "/requests",
            json={"workspace": "ws-dev", "template_id": "t1-agent-engine"},
            headers={"Authorization": f"Bearer {user_token}", "Idempotency-Key": "key-admin-rec"},
        )
        req_data = create_res.json()

        dead_letter_payload = {
            "request_id": req_data["request_id"],
            "deployment_id": req_data["deployment_id"],
            "template_id": "t1-agent-engine",
            "template_version": "2.0.0",
            "template_commit_sha": "010078cf6745f44da605f6fa0768b4f177c385a5",
            "repository": "idp-platform-org/idp-platform",
            "workflow": "deploy-t1.yml",
            "github_run_id": "999888111",
            "event_sequence": 1,
            "operation": "create",
            "status": "PLANNING",
            "summary": "Recovered dead letter planning event",
        }

        # 1. Non-admin cannot call reconcile -> 403 Forbidden
        denied_res = await client.post(
            "/admin/reconcile-callbacks",
            json={"dead_letter_events": [dead_letter_payload]},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert denied_res.status_code == 403

        # 2. Admin successfully reconciles -> 200 OK
        admin_res = await client.post(
            "/admin/reconcile-callbacks",
            json={"dead_letter_events": [dead_letter_payload]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_res.status_code == 200
        data = admin_res.json()
        assert data["reconciled_count"] == 1
        assert data["failed_count"] == 0
        assert req_data["request_id"] in data["reconciled_requests"]
