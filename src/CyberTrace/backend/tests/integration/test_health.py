import pytest


@pytest.mark.asyncio
async def test_health_check_reports_status(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "CyberTrace"
    assert "db_connected" in body
