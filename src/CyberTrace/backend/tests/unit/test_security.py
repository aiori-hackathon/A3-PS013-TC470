"""Tests for password hashing and JWT issuing/verification."""
import time

import jwt
import pytest

from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify_roundtrip():
    password = "CorrectHorseBatteryStaple1"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_password_verify_rejects_wrong_password():
    hashed = hash_password("CorrectPassword1")
    assert verify_password("WrongPassword1", hashed) is False


def test_access_token_roundtrip():
    token = create_access_token(subject="user-123", extra_claims={"role": "analyst"})
    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["role"] == "analyst"


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token(subject="user-123")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)
