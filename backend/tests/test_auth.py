"""Tests for the local JWT authentication endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient
from httpx import Response

_REGISTER = "/api/v1/auth/register"
_LOGIN = "/api/v1/auth/login"
_ME = "/api/v1/auth/me"

_EMAIL = "investor@example.com"
_PASSWORD = "s3cret-pass"


def _register(client: TestClient, **overrides: object) -> Response:
    payload: dict[str, object] = {
        "email": _EMAIL,
        "password": _PASSWORD,
        "full_name": "Test Investor",
    }
    payload.update(overrides)
    return client.post(_REGISTER, json=payload)


def test_register_returns_token(client: TestClient) -> None:
    response = _register(client)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    assert _register(client).status_code == 201
    response = _register(client)
    assert response.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    response = _register(client, password="short")
    assert response.status_code == 422


def test_register_rejects_invalid_email(client: TestClient) -> None:
    response = _register(client, email="not-an-email")
    assert response.status_code == 422


def test_login_success(client: TestClient) -> None:
    _register(client)
    response = client.post(_LOGIN, json={"email": _EMAIL, "password": _PASSWORD})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password(client: TestClient) -> None:
    _register(client)
    response = client.post(_LOGIN, json={"email": _EMAIL, "password": "wrong-pass"})
    assert response.status_code == 401


def test_login_unknown_email(client: TestClient) -> None:
    response = client.post(_LOGIN, json={"email": "nobody@example.com", "password": _PASSWORD})
    assert response.status_code == 401


def test_me_returns_profile_without_password(client: TestClient) -> None:
    token = _register(client).json()["access_token"]
    response = client.get(_ME, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == _EMAIL
    assert body["full_name"] == "Test Investor"
    assert "password_hash" not in body
    assert "password" not in body


def test_me_requires_authentication(client: TestClient) -> None:
    assert client.get(_ME).status_code == 401


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(_ME, headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401
