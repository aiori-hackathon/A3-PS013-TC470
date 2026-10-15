"""Integration tests for report export: JSON/CSV/PDF generation,
listing, download, and per-user case access control."""
import io
import json
import zipfile

import pytest

SYSLOG_CONTENT = (
    "Oct 10 08:00:00 server sshd[1]: Failed password for root from 10.0.0.5 port 1 ssh2\n"
    "garbage line\n"
    "Oct 10 12:00:00 server sshd[1]: Accepted password for alice from 10.0.0.9 port 2 ssh2\n"
)


async def _register_and_login(client, email: str, password: str = "StrongPassword1") -> str:
    await client.post("/api/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_case_with_evidence(client, token: str) -> str:
    case_resp = await client.post(
        "/api/cases", json={"name": "Reports test case"}, headers=_auth_headers(token)
    )
    case_id = case_resp.json()["id"]
    await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(SYSLOG_CONTENT.encode()), "text/plain")},
        headers=_auth_headers(token),
    )
    return case_id


@pytest.mark.asyncio
async def test_generate_report_requires_auth(client):
    resp = await client.post("/api/cases/some-case/reports", params={"format": "json"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_generate_json_report_contains_real_case_data(client):
    token = await _register_and_login(client, "report_json@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.post(
        f"/api/cases/{case_id}/reports", params={"format": "json"}, headers=_auth_headers(token)
    )
    assert resp.status_code == 201
    report = resp.json()
    assert report["format"] == "json"

    download_resp = await client.get(
        f"/api/reports/{report['id']}/download", headers=_auth_headers(token)
    )
    assert download_resp.status_code == 200
    payload = json.loads(download_resp.content)
    assert payload["case"]["id"] == case_id
    assert len(payload["log_records"]) == 2
    assert len(payload["parse_errors"]) == 1
    assert payload["evidence_files"][0]["original_filename"] == "auth.log"


@pytest.mark.asyncio
async def test_generate_csv_report_zips_two_files(client):
    token = await _register_and_login(client, "report_csv@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.post(
        f"/api/cases/{case_id}/reports", params={"format": "csv"}, headers=_auth_headers(token)
    )
    report = resp.json()

    download_resp = await client.get(
        f"/api/reports/{report['id']}/download", headers=_auth_headers(token)
    )
    assert download_resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(download_resp.content))
    assert set(zf.namelist()) == {"timeline_records.csv", "parse_errors.csv"}
    records_csv = zf.read("timeline_records.csv").decode()
    assert "auth_failure" in records_csv
    errors_csv = zf.read("parse_errors.csv").decode()
    assert "garbage line" in errors_csv


@pytest.mark.asyncio
async def test_generate_pdf_report_returns_valid_pdf_bytes(client):
    token = await _register_and_login(client, "report_pdf@example.com")
    case_id = await _create_case_with_evidence(client, token)

    resp = await client.post(
        f"/api/cases/{case_id}/reports", params={"format": "pdf"}, headers=_auth_headers(token)
    )
    report = resp.json()

    download_resp = await client.get(
        f"/api/reports/{report['id']}/download", headers=_auth_headers(token)
    )
    assert download_resp.status_code == 200
    assert download_resp.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_list_reports_for_case(client):
    token = await _register_and_login(client, "report_list@example.com")
    case_id = await _create_case_with_evidence(client, token)
    await client.post(
        f"/api/cases/{case_id}/reports", params={"format": "json"}, headers=_auth_headers(token)
    )

    list_resp = await client.get(f"/api/cases/{case_id}/reports", headers=_auth_headers(token))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_other_user_cannot_generate_or_download_report(client):
    token_owner = await _register_and_login(client, "report_owner@example.com")
    token_other = await _register_and_login(client, "report_intruder@example.com")
    case_id = await _create_case_with_evidence(client, token_owner)

    gen_resp = await client.post(
        f"/api/cases/{case_id}/reports",
        params={"format": "json"},
        headers=_auth_headers(token_other),
    )
    assert gen_resp.status_code == 403

    owner_report = await client.post(
        f"/api/cases/{case_id}/reports", params={"format": "json"}, headers=_auth_headers(token_owner)
    )
    report_id = owner_report.json()["id"]
    download_resp = await client.get(
        f"/api/reports/{report_id}/download", headers=_auth_headers(token_other)
    )
    assert download_resp.status_code == 403
