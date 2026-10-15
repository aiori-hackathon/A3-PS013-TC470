"""Integration tests for GET /api/cases/{id}/timeline: filtering, search,
ordering, and per-user case access control. Uses real evidence upload (not
fixture rows inserted directly) so log_records come from the real
ingestion pipeline, same as production."""
import io

import pytest

SYSLOG_CONTENT = (
    "Oct 10 08:00:00 server sshd[1]: Failed password for root from 10.0.0.5 port 1 ssh2\n"
    "Oct 10 08:05:00 server sshd[1]: Accepted password for alice from 10.0.0.9 port 2 ssh2\n"
    "Oct 10 09:00:00 server sshd[1]: Failed password for bob from 10.0.0.7 port 3 ssh2\n"
)


async def _register_and_login(client, email: str, password: str = "StrongPassword1") -> str:
    await client.post("/api/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_case_with_evidence(client, token: str, content: str = SYSLOG_CONTENT) -> str:
    case_resp = await client.post(
        "/api/cases", json={"name": "Timeline test case"}, headers=_auth_headers(token)
    )
    case_id = case_resp.json()["id"]
    await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(content.encode()), "text/plain")},
        headers=_auth_headers(token),
    )
    return case_id


@pytest.mark.asyncio
async def test_timeline_requires_auth(client):
    resp = await client.get("/api/cases/some-case/timeline")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_timeline_returns_records_in_ascending_order_by_default(client):
    token = await _register_and_login(client, "timeline_owner@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(f"/api/cases/{case_id}/timeline", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    timestamps = [r["event_time_utc"] for r in body["records"]]
    assert timestamps == sorted(timestamps)
    assert body["records"][0]["event_type"] == "auth_failure"
    assert body["records"][0]["evidence_filename"] == "auth.log"
    assert body["records"][0]["line_number"] == 1


@pytest.mark.asyncio
async def test_timeline_supports_descending_sort(client):
    token = await _register_and_login(client, "timeline_sort@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline",
        params={"sort": "event_time_utc", "order": "desc"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    timestamps = [r["event_time_utc"] for r in resp.json()["records"]]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.asyncio
async def test_timeline_filters_by_severity(client):
    token = await _register_and_login(client, "timeline_severity@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline",
        params={"severity": "warning"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert all(r["severity"] == "warning" for r in body["records"])


@pytest.mark.asyncio
async def test_timeline_filters_by_event_type(client):
    token = await _register_and_login(client, "timeline_eventtype@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline",
        params={"event_type": "auth_success"},
        headers=_auth_headers(token),
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["records"][0]["user_or_actor"] == "alice"


@pytest.mark.asyncio
async def test_timeline_filters_by_source(client):
    token = await _register_and_login(client, "timeline_source@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline",
        params={"source": "10.0.0.5"},
        headers=_auth_headers(token),
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["records"][0]["source_ip"] == "10.0.0.5"


@pytest.mark.asyncio
async def test_timeline_free_text_search_matches_message(client):
    token = await _register_and_login(client, "timeline_search@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline", params={"q": "bob"}, headers=_auth_headers(token)
    )
    body = resp.json()
    assert body["total"] == 1
    assert "bob" in body["records"][0]["message"]


@pytest.mark.asyncio
async def test_timeline_date_range_filter(client):
    token = await _register_and_login(client, "timeline_daterange@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline",
        params={"start_time": "2026-10-10T08:30:00Z"},
        headers=_auth_headers(token),
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["records"][0]["user_or_actor"] == "bob"


@pytest.mark.asyncio
async def test_timeline_pagination(client):
    token = await _register_and_login(client, "timeline_paginate@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline",
        params={"limit": 1, "offset": 1},
        headers=_auth_headers(token),
    )
    body = resp.json()
    assert body["total"] == 3
    assert len(body["records"]) == 1
    assert body["records"][0]["user_or_actor"] == "alice"


@pytest.mark.asyncio
async def test_other_user_cannot_view_timeline_of_private_case(client):
    token_owner = await _register_and_login(client, "timeline_owner2@example.com")
    token_other = await _register_and_login(client, "timeline_intruder@example.com")
    case_id = await _create_case_with_evidence(client, token_owner)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline", headers=_auth_headers(token_other)
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_timeline_rejects_unsupported_sort_field(client):
    token = await _register_and_login(client, "timeline_badsort@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(
        f"/api/cases/{case_id}/timeline",
        params={"sort": "message"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400
