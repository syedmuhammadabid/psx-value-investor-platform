"""Tests for the health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "environment" in body
    assert "version" in body


def test_health_sets_request_id_header(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.headers.get("X-Request-ID")
