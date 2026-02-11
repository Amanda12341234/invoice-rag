import pytest
from datetime import timedelta
from unittest.mock import patch

from app.auth import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert isinstance(hashed, str)


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(user_id=42)
    payload = decode_access_token(token)
    assert payload["sub"] == "42"


def test_expired_token():
    token = create_access_token(user_id=42, expires_delta=timedelta(seconds=-1))
    payload = decode_access_token(token)
    assert payload is None


def test_invalid_token():
    payload = decode_access_token("invalid.token.here")
    assert payload is None
