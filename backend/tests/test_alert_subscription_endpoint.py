"""Tests for the authenticated alert subscription endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.company import Company
from tests.conftest import register_user

_ALERTS = "/api/v1/alerts"


def test_alerts_require_authentication(client: TestClient) -> None:
    assert client.get(_ALERTS).status_code == 401


def test_subscribe_and_list(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    response = client.post(_ALERTS, json={"symbol": "MARI"}, headers=auth_headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["symbol"] == "MARI"
    assert isinstance(body["alerts"], list)

    listing = client.get(_ALERTS, headers=auth_headers)
    assert [item["symbol"] for item in listing.json()] == ["MARI"]


def test_subscribe_unknown_symbol_returns_404(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    assert client.post(_ALERTS, json={"symbol": "NOPE"}, headers=auth_headers).status_code == 404


def test_subscribe_duplicate_conflicts(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    assert client.post(_ALERTS, json={"symbol": "MARI"}, headers=auth_headers).status_code == 201
    assert client.post(_ALERTS, json={"symbol": "MARI"}, headers=auth_headers).status_code == 409


def test_unsubscribe(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    client.post(_ALERTS, json={"symbol": "MARI"}, headers=auth_headers)
    assert client.delete(f"{_ALERTS}/MARI", headers=auth_headers).status_code == 204
    assert client.get(_ALERTS, headers=auth_headers).json() == []


def test_unsubscribe_absent_returns_404(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    assert client.delete(f"{_ALERTS}/MARI", headers=auth_headers).status_code == 404


def test_subscriptions_are_scoped_to_owner(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    client.post(_ALERTS, json={"symbol": "MARI"}, headers=auth_headers)
    other = register_user(client, email="other@example.com")
    assert client.get(_ALERTS, headers=other).json() == []
