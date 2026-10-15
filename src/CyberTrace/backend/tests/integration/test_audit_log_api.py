"""Integration tests for audit log wiring + the admin-only viewer
endpoint, per PROJECT_PLAN.md section 11."""
import pytest
from sqlalchemy import select

from app.models.user import User


async def _register_and_login(client, email: str, password: str = "StrongPassword1") -> str:
    await client.post("/api/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_audit_log_requires_auth(client):
    resp = await client.get("/api/audit-log")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_non_admin_cannot_view_audit_log(client):
    token = await _register_and_login(client, "nonadmin@example.com")
    resp = await client.get("/api/audit-log", headers=_auth_headers(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_is_recorded_in_audit_log(client, db_session):
    token = await _register_and_login(client, "admin_audit@example.com")

    # Promote this user to admin directly in the DB (no admin-creation
    # endpoint exists yet) so we can exercise the admin-only viewer.
    result = await db_session.execute(select(User).where(User.email == "admin_audit@example.com"))
    user = result.scalar_one()
    user.role = "admin"
    await db_session.commit()

    resp = await client.get("/api/audit-log", headers=_auth_headers(token))
    assert resp.status_code == 200
    actions = [row["action"] for row in resp.json()]
    assert "login" in actions


@pytest.mark.asyncio
async def test_failed_login_is_recorded_in_audit_log(client, db_session):
    token = await _register_and_login(client, "admin_audit2@example.com")
    result = await db_session.execute(select(User).where(User.email == "admin_audit2@example.com"))
    user = result.scalar_one()
    user.role = "admin"
    await db_session.commit()

    await client.post(
        "/api/auth/login", json={"email": "admin_audit2@example.com", "password": "WrongPassword9"}
    )

    resp = await client.get("/api/audit-log", headers=_auth_headers(token))
    actions = [row["action"] for row in resp.json()]
    assert "login_failed" in actions


@pytest.mark.asyncio
async def test_evidence_upload_and_case_delete_are_recorded(client, db_session):
    import io

    token = await _register_and_login(client, "admin_audit3@example.com")
    result = await db_session.execute(select(User).where(User.email == "admin_audit3@example.com"))
    user = result.scalar_one()
    user.role = "admin"
    await db_session.commit()

    case_resp = await client.post(
        "/api/cases", json={"name": "Audit test case"}, headers=_auth_headers(token)
    )
    case_id = case_resp.json()["id"]
    await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("a.log", io.BytesIO(b"Oct 10 00:00:00 h p[1]: msg\n"), "text/plain")},
        headers=_auth_headers(token),
    )
    await client.delete(f"/api/cases/{case_id}", headers=_auth_headers(token))

    resp = await client.get("/api/audit-log", headers=_auth_headers(token))
    actions = [row["action"] for row in resp.json()]
    assert "evidence_upload" in actions
    assert "case_delete" in actions
