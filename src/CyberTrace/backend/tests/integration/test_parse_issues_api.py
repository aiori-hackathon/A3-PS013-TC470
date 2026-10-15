"""Integration tests for GET /api/cases/{id}/parse-issues: combined
parse_errors + parsing_gaps, with per-user case access control."""
import io

import pytest

# Line 2 is deliberately malformed; lines 1 and 3 have a >1hr timestamp
# jump, which should produce both a parse_errors row and a parsing_gaps row.
MIXED_CONTENT = (
    "Oct 10 08:00:00 server sshd[1]: Failed password for root from 10.0.0.5 port 1 ssh2\n"
    "this line is not valid syslog at all\n"
    "Oct 10 12:00:00 server sshd[1]: Accepted password for alice from 10.0.0.9 port 2 ssh2\n"
)


async def _register_and_login(client, email: str, password: str = "StrongPassword1") -> str:
    await client.post("/api/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_case_with_evidence(client, token: str, content: str = MIXED_CONTENT) -> str:
    case_resp = await client.post(
        "/api/cases", json={"name": "Parse issues test case"}, headers=_auth_headers(token)
    )
    case_id = case_resp.json()["id"]
    await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(content.encode()), "text/plain")},
        headers=_auth_headers(token),
    )
    return case_id


@pytest.mark.asyncio
async def test_parse_issues_requires_auth(client):
    resp = await client.get("/api/cases/some-case/parse-issues")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_parse_issues_returns_errors_and_gaps(client):
    token = await _register_and_login(client, "parseissues_owner@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.get(f"/api/cases/{case_id}/parse-issues", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["parse_errors"]) == 1
    error = body["parse_errors"][0]
    assert error["line_number"] == 2
    assert error["raw_line"] == "this line is not valid syslog at all"
    assert error["evidence_filename"] == "auth.log"
    assert "syslog" in error["reason"].lower()

    assert len(body["parsing_gaps"]) == 1
    gap = body["parsing_gaps"][0]
    assert gap["gap_start_line"] == 1
    assert gap["gap_end_line"] == 3
    assert gap["evidence_filename"] == "auth.log"


@pytest.mark.asyncio
async def test_parse_issues_empty_for_case_without_evidence(client):
    token = await _register_and_login(client, "parseissues_empty@example.com")
    case_resp = await client.post(
        "/api/cases", json={"name": "Empty case"}, headers=_auth_headers(token)
    )
    case_id = case_resp.json()["id"]

    resp = await client.get(f"/api/cases/{case_id}/parse-issues", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["parse_errors"] == []
    assert body["parsing_gaps"] == []


@pytest.mark.asyncio
async def test_other_user_cannot_view_parse_issues_of_private_case(client):
    token_owner = await _register_and_login(client, "parseissues_owner2@example.com")
    token_other = await _register_and_login(client, "parseissues_intruder@example.com")
    case_id = await _create_case_with_evidence(client, token_owner)

    resp = await client.get(
        f"/api/cases/{case_id}/parse-issues", headers=_auth_headers(token_other)
    )
    assert resp.status_code == 403
