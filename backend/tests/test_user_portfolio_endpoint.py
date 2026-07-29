"""Tests for the authenticated persisted-portfolio endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.company import Company
from tests.conftest import register_user

_PORTFOLIO = "/api/v1/portfolio"


def test_portfolio_requires_authentication(client: TestClient) -> None:
    assert client.get(_PORTFOLIO).status_code == 401


def test_empty_portfolio(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    response = client.get(_PORTFOLIO, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["holdings_count"] == 0
    assert body["holdings"] == []


def test_upsert_and_list_position(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    response = client.post(
        _PORTFOLIO,
        json={"symbol": "MARI", "quantity": 100, "average_cost": 500},
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["summary"]["holdings_count"] == 1
    assert body["summary"]["total_cost"] == 50000.0
    assert body["holdings"][0]["symbol"] == "MARI"

    listing = client.get(_PORTFOLIO, headers=auth_headers)
    assert listing.json()["summary"]["holdings_count"] == 1


def test_upsert_updates_existing_position(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    client.post(
        _PORTFOLIO,
        json={"symbol": "MARI", "quantity": 100, "average_cost": 500},
        headers=auth_headers,
    )
    response = client.post(
        _PORTFOLIO,
        json={"symbol": "MARI", "quantity": 200, "average_cost": 550},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["summary"]["holdings_count"] == 1
    assert body["summary"]["total_cost"] == 110000.0  # 200 * 550


def test_upsert_unknown_symbol_returns_404(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    response = client.post(
        _PORTFOLIO,
        json={"symbol": "NOPE", "quantity": 1, "average_cost": 1},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_remove_position(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    client.post(
        _PORTFOLIO,
        json={"symbol": "MARI", "quantity": 100, "average_cost": 500},
        headers=auth_headers,
    )
    removed = client.delete(f"{_PORTFOLIO}/MARI", headers=auth_headers)
    assert removed.status_code == 200
    assert removed.json()["summary"]["holdings_count"] == 0


def test_remove_absent_position_returns_404(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    assert client.delete(f"{_PORTFOLIO}/MARI", headers=auth_headers).status_code == 404


def test_portfolio_is_scoped_to_owner(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    client.post(
        _PORTFOLIO,
        json={"symbol": "MARI", "quantity": 100, "average_cost": 500},
        headers=auth_headers,
    )
    other = register_user(client, email="other@example.com")
    assert client.get(_PORTFOLIO, headers=other).json()["summary"]["holdings_count"] == 0
