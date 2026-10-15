"""Integration tests for evidence upload, download, listing, and
integrity verification."""
import hashlib
import io

import pytest


async def _register_and_login(client, email: str, password: str = "StrongPassword1") -> str:
    await client.post("/api/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_case(client, token: str, name: str = "Evidence test case") -> str:
    resp = await client.post("/api/cases", json={"name": name}, headers=_auth_headers(token))
    return resp.json()["id"]


SAMPLE_SYSLOG = (
    "Oct 10 13:55:36 server sshd[1234]: Failed password for root from 10.0.0.5 port 4444 ssh2\n"
    "Oct 10 13:55:40 server sshd[1234]: Failed password for root from 10.0.0.5 port 4444 ssh2\n"
)


@pytest.mark.asyncio
async def test_upload_requires_auth(client):
    resp = await client.post(
        "/api/cases/some-case/evidence",
        files={"file": ("auth.log", io.BytesIO(SAMPLE_SYSLOG.encode()), "text/plain")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_upload_evidence_computes_sha256_and_detects_format(client):
    token = await _register_and_login(client, "uploader@example.com")
    case_id = await _create_case(client, token)

    resp = await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(SAMPLE_SYSLOG.encode()), "text/plain")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    expected_hash = hashlib.sha256(SAMPLE_SYSLOG.encode()).hexdigest()
    assert body["evidence"]["sha256_hash"] == expected_hash
    assert body["evidence"]["detected_format"] == "syslog_auth"
    assert body["evidence"]["byte_size"] == len(SAMPLE_SYSLOG.encode())
    assert body["evidence"]["original_filename"] == "auth.log"
    # Phase 4: the syslog_auth parser now runs at upload time, so both
    # sample lines should parse successfully with no failures.
    assert body["records_parsed"] == 2
    assert body["records_failed"] == 0
    # Triage-time comparison (PROJECT_PLAN.md section 1): automated_seconds
    # is a real measurement (>= 0); manual_estimate_seconds is the labeled
    # assumption (2 lines x SECONDS_PER_LINE_MANUAL_ESTIMATE).
    assert body["automated_seconds"] >= 0
    assert body["manual_estimate_seconds"] == 2 * 15


@pytest.mark.asyncio
async def test_upload_rejects_disallowed_extension(client):
    token = await _register_and_login(client, "badext@example.com")
    case_id = await _create_case(client, token)

    resp = await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_rejects_empty_file(client):
    token = await _register_and_login(client, "empty@example.com")
    case_id = await _create_case(client, token)

    resp = await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("empty.log", io.BytesIO(b""), "text/plain")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_other_user_cannot_upload_to_case(client):
    token_a = await _register_and_login(client, "caseowner@example.com")
    token_b = await _register_and_login(client, "intruder@example.com")
    case_id = await _create_case(client, token_a)

    resp = await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(SAMPLE_SYSLOG.encode()), "text/plain")},
        headers=_auth_headers(token_b),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_evidence_for_case(client):
    token = await _register_and_login(client, "lister@example.com")
    case_id = await _create_case(client, token)
    await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(SAMPLE_SYSLOG.encode()), "text/plain")},
        headers=_auth_headers(token),
    )

    list_resp = await client.get(f"/api/cases/{case_id}/evidence", headers=_auth_headers(token))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_download_returns_original_bytes(client):
    token = await _register_and_login(client, "downloader@example.com")
    case_id = await _create_case(client, token)
    upload_resp = await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(SAMPLE_SYSLOG.encode()), "text/plain")},
        headers=_auth_headers(token),
    )
    evidence_id = upload_resp.json()["evidence"]["id"]

    download_resp = await client.get(
        f"/api/evidence/{evidence_id}/download", headers=_auth_headers(token)
    )
    assert download_resp.status_code == 200
    assert download_resp.content == SAMPLE_SYSLOG.encode()


@pytest.mark.asyncio
async def test_verify_evidence_passes_for_untouched_file(client):
    token = await _register_and_login(client, "verifier@example.com")
    case_id = await _create_case(client, token)
    upload_resp = await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(SAMPLE_SYSLOG.encode()), "text/plain")},
        headers=_auth_headers(token),
    )
    evidence_id = upload_resp.json()["evidence"]["id"]

    verify_resp = await client.get(
        f"/api/evidence/{evidence_id}/verify", headers=_auth_headers(token)
    )
    assert verify_resp.status_code == 200
    body = verify_resp.json()
    assert body["verified"] is True
    assert body["recomputed_sha256"] == body["recorded_sha256"]


@pytest.mark.asyncio
async def test_verify_evidence_detects_tampering(client, tmp_path):
    """Corrupts the stored file on disk directly (simulating tampering
    outside the application) and asserts the API honestly reports the
    mismatch rather than a false positive. Storage is already redirected
    to tmp_path by the autouse `_isolated_evidence_storage` fixture."""
    token = await _register_and_login(client, "tamperdetect@example.com")
    case_id = await _create_case(client, token)
    upload_resp = await client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("auth.log", io.BytesIO(SAMPLE_SYSLOG.encode()), "text/plain")},
        headers=_auth_headers(token),
    )
    evidence_id = upload_resp.json()["evidence"]["id"]

    case_dir = tmp_path / case_id
    stored_files = list(case_dir.glob("*"))
    assert stored_files, "expected the uploaded evidence file to exist on disk"
    stored_files[0].write_bytes(b"TAMPERED CONTENT")

    verify_resp = await client.get(
        f"/api/evidence/{evidence_id}/verify", headers=_auth_headers(token)
    )
    assert verify_resp.status_code == 200
    body = verify_resp.json()
    assert body["verified"] is False
    assert body["recomputed_sha256"] != body["recorded_sha256"]
