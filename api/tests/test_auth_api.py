"""
Integration tests for FastAPI Authentication endpoints (/auth/login, /auth/me, /healthz).
"""

import pytest
from api.app.auth.hasher import hash_password
from api.app.main import app
from api.app.repositories.user_repository import UserRecord, user_repo
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
async def seed_test_users():
    """Seed sample test users into the in-memory repository before each test."""
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
    bob_disabled = UserRecord(
        user_id="usr-bob",
        username="bob",
        email="bob@example.com",
        password_hash=hash_password("ValidPassword123!"),
        role="developer",
        workspaces=["ws-dev"],
        token_version=1,
        is_active=False,  # Disabled user
    )
    admin = UserRecord(
        user_id="usr-admin",
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("AdminMasterPassword123!"),
        role="platform_admin",
        workspaces=["default", "admin"],
        token_version=1,
        is_active=True,
    )
    await user_repo.save(alice)
    await user_repo.save(bob_disabled)
    await user_repo.save(admin)


@pytest.mark.asyncio
async def test_healthz_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "IDP Control Plane API" in data["app"]


@pytest.mark.asyncio
async def test_login_success_returns_jwt_with_60m_expiry():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"username": "alice", "password": "ValidPassword123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600  # 60 minutes


@pytest.mark.asyncio
async def test_login_invalid_password_returns_generic_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"username": "alice", "password": "WrongPassword!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password."


@pytest.mark.asyncio
async def test_login_nonexistent_user_returns_generic_401_no_enumeration():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"username": "nonexistent_user", "password": "SomePassword123!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password."


@pytest.mark.asyncio
async def test_login_disabled_user_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"username": "bob", "password": "ValidPassword123!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password."


@pytest.mark.asyncio
async def test_get_me_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Login
        login_res = await client.post(
            "/auth/login",
            json={"username": "alice", "password": "ValidPassword123!"},
        )
        token = login_res.json()["access_token"]

        # Step 2: Call /auth/me with Bearer token
        me_res = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        user = me_res.json()
        assert user["username"] == "alice"
        assert user["email"] == "alice@example.com"
        assert user["role"] == "developer"
        assert user["workspaces"] == ["ws-dev"]
        assert "password_hash" not in user  # Must not leak password hash


@pytest.mark.asyncio
async def test_get_me_missing_token_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/me")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_revoked_token_version_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Login as admin
        login_res = await client.post(
            "/auth/login",
            json={"username": "admin", "password": "AdminMasterPassword123!"},
        )
        token = login_res.json()["access_token"]

        # Step 2: Increment token_version in user record (revoking previously issued token)
        admin_user = await user_repo.get_by_id("usr-admin")
        admin_user.token_version = 2
        await user_repo.save(admin_user)

        # Step 3: Attempt /auth/me with old token
        me_res = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 401
        assert "revoked" in me_res.json()["detail"].lower()
