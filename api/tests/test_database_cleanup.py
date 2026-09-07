"""
Tests for Database Cleanup Endpoint and Operational Script.
"""

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from api.app.auth.hasher import hash_password
from api.app.domain.models import DeploymentRecord, DeploymentStatus
from api.app.main import app
from api.app.repositories.platform_repositories import deployment_repo
from api.app.repositories.user_repository import UserRecord, user_repo
from scripts.cleanup_database import (
    count_documents,
    delete_collection,
    reseed_baseline_templates,
    reseed_baseline_users,
)


@pytest.fixture(autouse=True)
async def seed_cleanup_test_users():
    admin = UserRecord(
        user_id="usr-admin-clean",
        username="admin_clean",
        email="admin_clean@example.com",
        password_hash=hash_password("AdminCleanPass123!"),
        role="platform_admin",
        workspaces=["default", "admin", "ws-dev"],
        token_version=1,
        is_active=True,
    )
    dev = UserRecord(
        user_id="usr-dev-clean",
        username="dev_clean",
        email="dev_clean@example.com",
        password_hash=hash_password("DevCleanPass123!"),
        role="developer",
        workspaces=["ws-dev"],
        token_version=1,
        is_active=True,
    )
    await user_repo.save(admin)
    await user_repo.save(dev)


async def get_token(username: str, password: str) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_cleanup_database_unauthenticated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/admin/cleanup-database",
            json={"include_users": False, "include_templates": False, "reseed": True},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_cleanup_database_forbidden_for_developer():
    token = await get_token("dev_clean", "DevCleanPass123!")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/admin/cleanup-database",
            headers={"Authorization": f"Bearer {token}"},
            json={"include_users": False, "include_templates": False, "reseed": True},
        )
        assert resp.status_code == 403
        assert "Administrative privilege required" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_cleanup_database_success_as_admin():
    # 1. Seed a sample deployment
    sample_dep = DeploymentRecord(
        deployment_id="dep-cleanup-test-01",
        workspace="ws-dev",
        template_id="t1-agent-engine",
        template_version="2.0.0",
        template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
        environment="dev",
        status=DeploymentStatus.ACTIVE,
        owner_user_id="usr-dev-clean",
    )
    await deployment_repo.save(sample_dep)
    assert await deployment_repo.get("dep-cleanup-test-01") is not None

    # 2. Call cleanup endpoint as admin
    token = await get_token("admin_clean", "AdminCleanPass123!")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/admin/cleanup-database",
            headers={"Authorization": f"Bearer {token}"},
            json={"include_users": False, "include_templates": False, "reseed": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "deployments" in data["purged_collections"]
        assert data["reseeded_users"] >= 3
        assert data["reseeded_templates"] >= 4

    # 3. Verify deployment was purged
    assert await deployment_repo.get("dep-cleanup-test-01") is None


def test_script_helper_functions_mocked():
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.collection.return_value = mock_coll

    # Mock count_documents
    mock_doc1 = MagicMock()
    mock_doc2 = MagicMock()
    mock_coll.stream.return_value = [mock_doc1, mock_doc2]
    cnt = count_documents(mock_db, "test_collection")
    assert cnt == 2

    # Mock delete_collection
    mock_coll.limit.return_value.stream.side_effect = [[mock_doc1], []]
    mock_batch = MagicMock()
    mock_db.batch.return_value = mock_batch
    deleted = delete_collection(mock_db, "test_collection")
    assert deleted == 1
    mock_batch.delete.assert_called_once_with(mock_doc1.reference)
    mock_batch.commit.assert_called_once()

    # Mock reseed_baseline_users
    mock_user_doc = MagicMock()
    mock_coll.document.return_value = mock_user_doc
    seeded_users = reseed_baseline_users(mock_db)
    assert seeded_users >= 3
    assert mock_user_doc.set.call_count >= 3

    # Mock reseed_baseline_templates
    mock_tpl_doc = MagicMock()
    mock_coll.document.return_value = mock_tpl_doc
    seeded_tpls = reseed_baseline_templates(mock_db)
    assert seeded_tpls >= 4
    assert mock_tpl_doc.set.call_count >= 4
