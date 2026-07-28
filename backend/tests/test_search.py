"""Tests for the search endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_search_by_symbol(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/search", params={"q": "MAR"})
    assert response.status_code == 200

    results = response.json()
    assert len(results) == 1
    assert results[0]["symbol"] == "MARI"


def test_search_by_name(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/search", params={"q": "systems"})
    results = response.json()

    assert [r["symbol"] for r in results] == ["SYS"]


def test_search_excludes_inactive(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/search", params={"q": "holdings"})
    assert response.json() == []


def test_search_requires_query(client: TestClient) -> None:
    response = client.get("/api/v1/search")
    assert response.status_code == 422
