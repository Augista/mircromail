"""
E2E tests for auth flow through the API Gateway.
Requires the full Docker stack to be running (docker-compose up).
"""

import time
import pytest
from conftest import (
    SENDER_EMAIL, SENDER_PASSWORD, SENDER_NAME,
    auth_headers, make_email,
)


class TestHealth:
    def test_gateway_healthy(self, http):
        r = http.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestRegister:
    def test_success(self, http):
        email = make_email("reg_ok")
        r = http.post("/api/auth/register", json={
            "name": "Reg User",
            "email": email,
            "password": "password123",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["user"]["email"] == email
        assert "access_token" in body
        assert "refresh_token" in body

    def test_duplicate_email_returns_409(self, http):
        email = make_email("reg_dupe")
        payload = {"name": "Dupe", "email": email, "password": "password123"}
        http.post("/api/auth/register", json=payload)
        r = http.post("/api/auth/register", json=payload)
        assert r.status_code == 409

    def test_invalid_email_returns_422(self, http):
        r = http.post("/api/auth/register", json={
            "name": "Bad",
            "email": "not-an-email",
            "password": "password123",
        })
        assert r.status_code == 422

    def test_missing_fields_returns_422(self, http):
        r = http.post("/api/auth/register", json={"email": "a@b.com"})
        assert r.status_code == 422


class TestLogin:
    def test_success(self, http, sender_token):
        # sender_token fixture already logs in — just verify it's a non-empty string
        assert isinstance(sender_token, str)
        assert len(sender_token) > 0

    def test_wrong_password_returns_401(self, http):
        r = http.post("/api/auth/login", json={
            "email": SENDER_EMAIL,
            "password": "wrongpassword",
        })
        assert r.status_code == 401

    def test_unknown_email_returns_401(self, http):
        r = http.post("/api/auth/login", json={
            "email": "nobody_ever@test.com",
            "password": "password123",
        })
        assert r.status_code == 401

    def test_missing_password_returns_422(self, http):
        r = http.post("/api/auth/login", json={"email": SENDER_EMAIL})
        assert r.status_code == 422


class TestMe:
    def test_returns_current_user(self, http, sender_token):
        r = http.get("/api/auth/me", headers=auth_headers(sender_token))
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == SENDER_EMAIL
        assert body["name"] == SENDER_NAME

    def test_no_token_returns_401(self, http):
        r = http.get("/api/auth/me")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, http):
        r = http.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token"})
        assert r.status_code == 401


class TestRefresh:
    def test_returns_new_access_token(self, http):
        # Register a fresh user so we control the refresh token
        email = make_email("refresh_user")
        r = http.post("/api/auth/register", json={
            "name": "Refresh User",
            "email": email,
            "password": "password123",
        })
        assert r.status_code == 200
        refresh_token = r.json()["refresh_token"]

        r2 = http.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert r2.status_code == 200
        body = r2.json()
        assert "access_token" in body
        assert body["access_token"] != ""

    def test_invalid_refresh_token_returns_401(self, http):
        r = http.post("/api/auth/refresh", json={"refresh_token": "invalid.token.here"})
        assert r.status_code == 401
