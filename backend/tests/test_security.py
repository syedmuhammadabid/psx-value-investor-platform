"""Unit tests for password hashing and JWT helpers."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)


def test_verify_rejects_wrong_password() -> None:
    hashed = hash_password("s3cret-pass")
    assert not verify_password("other-pass", hashed)


def test_verify_handles_malformed_hash() -> None:
    assert not verify_password("s3cret-pass", "not-a-bcrypt-hash")


def test_token_round_trip() -> None:
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"


def test_decode_rejects_garbage() -> None:
    with pytest.raises(TokenError):
        decode_access_token("not.a.jwt")


def test_decode_rejects_expired_token() -> None:
    token = create_access_token("user-123", expires_delta=timedelta(minutes=-1))
    with pytest.raises(TokenError):
        decode_access_token(token)
