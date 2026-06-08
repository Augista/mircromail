"""
Tests for auth-service endpoints: /health, /register, /login, /refresh, /me.

Strategy: DB sessions are mocked via patch("main.SessionLocal") so tests run
without a real PostgreSQL instance. For /register, main.User is also patched
to return a pre-built mock user (so attributes like id/created_at are set
before UserResponse.from_orm is called, since SQLAlchemy only populates
column defaults after a real flush).
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from conftest import (
    TEST_USER_EMAIL,
    TEST_USER_NAME,
    TEST_USER_PASSWORD,
    make_mock_user,
)
from utils import JWTManager


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_client():
    from main import app
    return TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_healthy(self):
        r = _get_client().get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["service"] == "Auth Service"


# ── Register ──────────────────────────────────────────────────────────────────

class TestRegister:
    def test_success(self, mock_db):
        new_user = make_mock_user(email="new@example.com", name="New User")
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("main.SessionLocal", return_value=mock_db), \
             patch("main.User", return_value=new_user):
            r = _get_client().post("/register", json={
                "email": "new@example.com",
                "name": "New User",
                "password": "securepassword123",
            })

        assert r.status_code == 200
        body = r.json()
        assert body["user"]["email"] == "new@example.com"
        assert body["user"]["name"] == "New User"
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    def test_duplicate_email_returns_409(self, mock_db):
        existing = make_mock_user(email="dupe@example.com")
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/register", json={
                "email": "dupe@example.com",
                "name": "Someone",
                "password": "password123",
            })

        assert r.status_code == 409
        assert "already registered" in r.json()["detail"]

    def test_invalid_email_format_returns_422(self):
        r = _get_client().post("/register", json={
            "email": "not-an-email",
            "name": "User",
            "password": "password123",
        })
        assert r.status_code == 422

    def test_missing_password_returns_422(self):
        r = _get_client().post("/register", json={
            "email": "user@example.com",
            "name": "User",
        })
        assert r.status_code == 422

    def test_missing_name_returns_422(self):
        r = _get_client().post("/register", json={
            "email": "user@example.com",
            "password": "password123",
        })
        assert r.status_code == 422

    def test_empty_body_returns_422(self):
        r = _get_client().post("/register", json={})
        assert r.status_code == 422

    def test_response_tokens_are_valid_jwt(self, mock_db):
        new_user = make_mock_user(email="jwt@example.com", name="JWT User")
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("main.SessionLocal", return_value=mock_db), \
             patch("main.User", return_value=new_user):
            r = _get_client().post("/register", json={
                "email": "jwt@example.com",
                "name": "JWT User",
                "password": "password123",
            })

        assert r.status_code == 200
        body = r.json()
        access_payload = JWTManager.verify_token(body["access_token"])
        refresh_payload = JWTManager.verify_token(body["refresh_token"])
        assert access_payload is not None
        assert access_payload["type"] == "access"
        assert access_payload["email"] == "jwt@example.com"
        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_success(self, mock_db):
        user = make_mock_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
            })

        assert r.status_code == 200
        body = r.json()
        assert body["user"]["email"] == TEST_USER_EMAIL
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, mock_db):
        user = make_mock_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/login", json={
                "email": TEST_USER_EMAIL,
                "password": "wrongpassword",
            })

        assert r.status_code == 401
        assert "Invalid email or password" in r.json()["detail"]

    def test_nonexistent_user_returns_401(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/login", json={
                "email": "nobody@example.com",
                "password": "password",
            })

        assert r.status_code == 401
        assert "Invalid email or password" in r.json()["detail"]

    def test_missing_email_returns_422(self):
        r = _get_client().post("/login", json={"password": "password123"})
        assert r.status_code == 422

    def test_login_tokens_are_valid_jwt(self, mock_db):
        user = make_mock_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
            })

        assert r.status_code == 200
        body = r.json()
        access_payload = JWTManager.verify_token(body["access_token"])
        assert access_payload["type"] == "access"
        assert access_payload["email"] == TEST_USER_EMAIL


# ── Refresh Token ─────────────────────────────────────────────────────────────

class TestRefresh:
    def test_success(self, mock_db):
        user = make_mock_user()
        refresh_token = JWTManager.create_refresh_token(str(user.id), user.email)

        mock_token_obj = MagicMock()
        mock_token_obj.user = user
        mock_db.query.return_value.filter.return_value.first.return_value = mock_token_obj

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/refresh", json={"refresh_token": refresh_token})

        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["refresh_token"] == refresh_token
        assert body["token_type"] == "bearer"

    def test_new_access_token_is_valid(self, mock_db):
        user = make_mock_user()
        refresh_token = JWTManager.create_refresh_token(str(user.id), user.email)

        mock_token_obj = MagicMock()
        mock_token_obj.user = user
        mock_db.query.return_value.filter.return_value.first.return_value = mock_token_obj

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/refresh", json={"refresh_token": refresh_token})

        payload = JWTManager.verify_token(r.json()["access_token"])
        assert payload is not None
        assert payload["type"] == "access"
        assert payload["email"] == user.email

    def test_invalid_token_returns_401(self, mock_db):
        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/refresh", json={"refresh_token": "invalid.token.here"})
        assert r.status_code == 401

    def test_revoked_token_returns_401(self, mock_db):
        user = make_mock_user()
        refresh_token = JWTManager.create_refresh_token(str(user.id), user.email)

        # Simulate token not found in DB (revoked)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/refresh", json={"refresh_token": refresh_token})

        assert r.status_code == 401
        assert "revoked" in r.json()["detail"]

    def test_access_token_rejected_as_refresh(self, mock_db):
        user = make_mock_user()
        # Pass an access token where a refresh token is expected
        access_token = JWTManager.create_access_token(str(user.id), user.email)

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().post("/refresh", json={"refresh_token": access_token})

        assert r.status_code == 401

    def test_missing_body_returns_422(self):
        r = _get_client().post("/refresh", json={})
        assert r.status_code == 422


# ── /me ───────────────────────────────────────────────────────────────────────

class TestMe:
    def test_success(self, mock_db):
        user = make_mock_user()
        access_token = JWTManager.create_access_token(str(user.id), user.email)
        mock_db.query.return_value.filter.return_value.first.return_value = user

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().get("/me", headers={"Authorization": f"Bearer {access_token}"})

        assert r.status_code == 200
        body = r.json()
        assert body["email"] == user.email
        assert body["name"] == user.name

    def test_no_auth_header_returns_401(self):
        r = _get_client().get("/me")
        assert r.status_code == 401

    def test_malformed_auth_header_returns_401(self):
        r = _get_client().get("/me", headers={"Authorization": "Token sometoken"})
        assert r.status_code == 401

    def test_invalid_token_returns_401(self):
        r = _get_client().get("/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert r.status_code == 401

    def test_refresh_token_rejected_for_me(self, mock_db):
        user = make_mock_user()
        refresh_token = JWTManager.create_refresh_token(str(user.id), user.email)

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().get("/me", headers={"Authorization": f"Bearer {refresh_token}"})

        assert r.status_code == 401

    def test_user_not_found_returns_404(self, mock_db):
        user = make_mock_user()
        access_token = JWTManager.create_access_token(str(user.id), user.email)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("main.SessionLocal", return_value=mock_db):
            r = _get_client().get("/me", headers={"Authorization": f"Bearer {access_token}"})

        assert r.status_code == 404
