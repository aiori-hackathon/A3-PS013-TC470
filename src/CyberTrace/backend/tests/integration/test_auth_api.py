"""Integration tests for the /api/auth endpoints, exercised through the
real FastAPI app with an isolated in-memory database (see conftest.py)."""
import pytest


@pytest.mark.asyncio
async def test_register_creates_user(client):
    resp = await client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "StrongPassword1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newuser@example.com"
    assert body["role"] == "analyst"
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "StrongPassword1"}
    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_register_rejects_short_password(client):
    resp = await client.post(
        "/api/auth/register", json={"email": "short@example.com", "password": "short"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_succeeds_with_correct_credentials(client):
    payload = {"email": "login@example.com", "password": "StrongPassword1"}
    await client.post("/api/auth/register", json=payload)

    resp = await client.post("/api/auth/login", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client):
    payload = {"email": "wrongpw@example.com", "password": "StrongPassword1"}
    await client.post("/api/auth/register", json=payload)

    resp = await client.post(
        "/api/auth/login", json={"email": "wrongpw@example.com", "password": "WrongOne1"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_unknown_email(client):
    resp = await client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "Whatever1"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user_with_valid_token(client):
    payload = {"email": "me@example.com", "password": "StrongPassword1"}
    await client.post("/api/auth/register", json=payload)
    login_resp = await client.post("/api/auth/login", json=payload)
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_rejects_invalid_token(client):
    resp = await client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401
