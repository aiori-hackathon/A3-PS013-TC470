"""Integration tests for synthetic scenario listing + loading, per
PROJECT_PLAN.md section 9: reproducible from committed sample logs, not
mystery seed data, and labeled is_synthetic=True."""
import pytest


async def _register_and_login(client, email: str, password: str = "StrongPassword1") -> str:
    await client.post("/api/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_scenarios_returns_all_three(client):
    resp = await client.get("/api/scenarios")
    assert resp.status_code == 200
    keys = {s["key"] for s in resp.json()}
    assert keys == {"ssh_bruteforce", "sql_injection_probe", "phishing_lateral_movement"}


@pytest.mark.asyncio
async def test_load_scenario_requires_auth(client):
    resp = await client.post("/api/scenarios/ssh_bruteforce/load")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_load_unknown_scenario_returns_404(client):
    token = await _register_and_login(client, "scenario_unknown@example.com")
    resp = await client.post("/api/scenarios/does_not_exist/load", headers=_auth_headers(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_load_ssh_bruteforce_scenario_creates_synthetic_case_with_real_parsing(client):
    token = await _register_and_login(client, "scenario_ssh@example.com")
    resp = await client.post("/api/scenarios/ssh_bruteforce/load", headers=_auth_headers(token))
    assert resp.status_code == 201
    body = resp.json()

    assert body["case"]["is_synthetic"] is True
    assert body["case"]["scenario_key"] == "ssh_bruteforce"
    assert body["records_parsed"] > 0
    assert body["records_failed"] > 0  # fixture includes corrupted lines

    case_id = body["case"]["id"]
    timeline_resp = await client.get(
        f"/api/cases/{case_id}/timeline", headers=_auth_headers(token)
    )
    assert timeline_resp.status_code == 200
    assert timeline_resp.json()["total"] == body["records_parsed"]


@pytest.mark.asyncio
async def test_load_sql_injection_probe_scenario(client):
    token = await _register_and_login(client, "scenario_sqli@example.com")
    resp = await client.post(
        "/api/scenarios/sql_injection_probe/load", headers=_auth_headers(token)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["records_parsed"] > 0
    assert body["records_failed"] > 0


@pytest.mark.asyncio
async def test_load_phishing_lateral_movement_scenario(client):
    token = await _register_and_login(client, "scenario_phish@example.com")
    resp = await client.post(
        "/api/scenarios/phishing_lateral_movement/load", headers=_auth_headers(token)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["records_parsed"] == 5
    assert body["records_failed"] == 0


@pytest.mark.asyncio
async def test_synthetic_case_visible_to_other_users(client):
    token_loader = await _register_and_login(client, "scenario_loader@example.com")
    token_other = await _register_and_login(client, "scenario_viewer@example.com")
    load_resp = await client.post(
        "/api/scenarios/ssh_bruteforce/load", headers=_auth_headers(token_loader)
    )
    case_id = load_resp.json()["case"]["id"]

    # Synthetic cases are shared/read-only demo data visible to every
    # authenticated user (same rule as cases.py for real cases).
    resp = await client.get(f"/api/cases/{case_id}", headers=_auth_headers(token_other))
    assert resp.status_code == 200
    assert resp.json()["is_synthetic"] is True
