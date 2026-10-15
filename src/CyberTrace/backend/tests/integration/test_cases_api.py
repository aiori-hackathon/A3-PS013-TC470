"""Integration tests for /api/cases, including per-user authorization."""
import pytest


async def _register_and_login(client, email: str, password: str = "StrongPassword1") -> str:
    await client.post("/api/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_case_requires_auth(client):
    resp = await client.post("/api/cases", json={"name": "Unauthorized case"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_case(client):
    token = await _register_and_login(client, "owner@example.com")

    create_resp = await client.post(
        "/api/cases",
        json={"name": "Suspicious SSH activity", "description": "Investigating brute force"},
        headers=_auth_headers(token),
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["name"] == "Suspicious SSH activity"
    assert body["is_synthetic"] is False

    list_resp = await client.get("/api/cases", headers=_auth_headers(token))
    assert list_resp.status_code == 200
    names = [c["name"] for c in list_resp.json()]
    assert "Suspicious SSH activity" in names


@pytest.mark.asyncio
async def test_case_name_required(client):
    token = await _register_and_login(client, "validate@example.com")
    resp = await client.post("/api/cases", json={"name": ""}, headers=_auth_headers(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_user_cannot_see_other_users_private_case(client):
    token_a = await _register_and_login(client, "usera@example.com")
    token_b = await _register_and_login(client, "userb@example.com")

    create_resp = await client.post(
        "/api/cases", json={"name": "Private to A"}, headers=_auth_headers(token_a)
    )
    case_id = create_resp.json()["id"]

    list_resp_b = await client.get("/api/cases", headers=_auth_headers(token_b))
    ids_b = [c["id"] for c in list_resp_b.json()]
    assert case_id not in ids_b

    detail_resp_b = await client.get(f"/api/cases/{case_id}", headers=_auth_headers(token_b))
    assert detail_resp_b.status_code == 403


@pytest.mark.asyncio
async def test_case_detail_includes_counts(client):
    token = await _register_and_login(client, "counts@example.com")
    create_resp = await client.post(
        "/api/cases", json={"name": "Count check"}, headers=_auth_headers(token)
    )
    case_id = create_resp.json()["id"]

    detail_resp = await client.get(f"/api/cases/{case_id}", headers=_auth_headers(token))
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["evidence_count"] == 0
    assert body["log_record_count"] == 0
    assert body["parse_error_count"] == 0


@pytest.mark.asyncio
async def test_get_nonexistent_case_returns_404(client):
    token = await _register_and_login(client, "notfound@example.com")
    resp = await client.get("/api/cases/does-not-exist", headers=_auth_headers(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_owner_can_delete_case(client):
    token = await _register_and_login(client, "deleter@example.com")
    create_resp = await client.post(
        "/api/cases", json={"name": "To delete"}, headers=_auth_headers(token)
    )
    case_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/cases/{case_id}", headers=_auth_headers(token))
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/cases/{case_id}", headers=_auth_headers(token))
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_other_user_cannot_delete_case(client):
    token_a = await _register_and_login(client, "ownerd@example.com")
    token_b = await _register_and_login(client, "otherd@example.com")
    create_resp = await client.post(
        "/api/cases", json={"name": "Protected"}, headers=_auth_headers(token_a)
    )
    case_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/cases/{case_id}", headers=_auth_headers(token_b))
    assert delete_resp.status_code == 403
