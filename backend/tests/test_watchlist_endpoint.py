"""Tests for the authenticated watchlist endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.company import Company
from tests.conftest import register_user

_WATCHLIST = "/api/v1/watchlist"


def test_watchlist_requires_authentication(client: TestClient) -> None:
    assert client.get(_WATCHLIST).status_code == 401


def test_add_and_list_watchlist(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    response = client.post(_WATCHLIST, json={"symbol": "MARI"}, headers=auth_headers)
    assert response.status_code == 201, response.text
    assert response.json()["symbol"] == "MARI"
    assert response.json()["name"] == "Mari Petroleum Company Limited"

    listing = client.get(_WATCHLIST, headers=auth_headers)
    assert listing.status_code == 200
    symbols = [item["symbol"] for item in listing.json()]
    assert symbols == ["MARI"]


def test_add_unknown_symbol_returns_404(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    response = client.post(_WATCHLIST, json={"symbol": "NOPE"}, headers=auth_headers)
    assert response.status_code == 404


def test_add_duplicate_symbol_conflicts(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    assert client.post(_WATCHLIST, json={"symbol": "MARI"}, headers=auth_headers).status_code == 201
    response = client.post(_WATCHLIST, json={"symbol": "MARI"}, headers=auth_headers)
    assert response.status_code == 409


def test_remove_watchlist_item(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    client.post(_WATCHLIST, json={"symbol": "MARI"}, headers=auth_headers)
    removed = client.delete(f"{_WATCHLIST}/MARI", headers=auth_headers)
    assert removed.status_code == 204
    assert client.get(_WATCHLIST, headers=auth_headers).json() == []


def test_remove_absent_item_returns_404(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    assert client.delete(f"{_WATCHLIST}/MARI", headers=auth_headers).status_code == 404


def test_watchlist_is_scoped_to_owner(
    client: TestClient, seed_companies: list[Company], auth_headers: dict[str, str]
) -> None:
    client.post(_WATCHLIST, json={"symbol": "MARI"}, headers=auth_headers)
    other = register_user(client, email="other@example.com")
    assert client.get(_WATCHLIST, headers=other).json() == []
