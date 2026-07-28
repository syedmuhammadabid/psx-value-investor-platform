"""Tests for the companies endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_companies_returns_active_sorted_by_market_cap(
    client: TestClient, seed_companies: list
) -> None:
    response = client.get("/api/v1/companies")
    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 3  # OLDCO is inactive and excluded
    symbols = [item["symbol"] for item in body["items"]]
    assert symbols == ["MARI", "UBL", "SYS"]  # descending market cap
    assert body["items"][0]["sector"] == "Energy"


def test_list_companies_pagination(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/companies", params={"limit": 1, "offset": 1})
    body = response.json()

    assert body["total"] == 3
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["symbol"] == "UBL"


def test_list_companies_search_filter(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/companies", params={"q": "bank"})
    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["symbol"] == "UBL"


def test_list_companies_sector_filter(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/companies", params={"sector": "Technology & Communication"})
    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["symbol"] == "SYS"


def test_list_companies_sort_by_name(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/companies", params={"sort": "name"})
    symbols = [item["symbol"] for item in response.json()["items"]]

    assert symbols == ["MARI", "SYS", "UBL"]


def test_get_company_by_symbol_case_insensitive(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/companies/sys")
    assert response.status_code == 200

    body = response.json()
    assert body["symbol"] == "SYS"
    assert body["name"] == "Systems Limited"
    assert body["sector"] == "Technology & Communication"


def test_get_company_not_found(client: TestClient, seed_companies: list) -> None:
    response = client.get("/api/v1/companies/NOPE")
    assert response.status_code == 404


def test_list_companies_invalid_limit(client: TestClient) -> None:
    response = client.get("/api/v1/companies", params={"limit": 0})
    assert response.status_code == 422
