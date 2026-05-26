from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["status"] == "healthy"


def test_list_posts_empty(client: TestClient):
    response = client.get("/api/v1/posts")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_crawl_trigger_without_token(client: TestClient):
    """Without ADMIN_API_TOKEN configured, the endpoint returns 500.
    With a configured token but no header, it would return 401."""
    response = client.post("/api/v1/crawl/trigger")
    assert response.status_code in (401, 500)


def test_list_pain_points_empty(client: TestClient):
    response = client.get("/api/v1/pain-points")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_crawl_status(client: TestClient):
    response = client.get("/api/v1/crawl/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "is_running" in data["data"]
