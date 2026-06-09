import time
import pytest
import httpx

BASE_URL = "http://localhost:8000"

# Unique suffix per test session so re-runs don't hit 409 on register
_TS = int(time.time())


def make_email(prefix: str) -> str:
    return f"{prefix}_{_TS}@test.com"


# ── shared users ──────────────────────────────────────────────────────────────

SENDER_EMAIL = make_email("sender")
SENDER_PASSWORD = "password123"
SENDER_NAME = "Sender User"

RECEIVER_EMAIL = make_email("receiver")
RECEIVER_PASSWORD = "password123"
RECEIVER_NAME = "Receiver User"


@pytest.fixture(scope="session")
def http():
    """Shared httpx client for the whole test session."""
    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        yield client


@pytest.fixture(scope="session")
def sender_token(http):
    """Register + login as sender, return access_token."""
    http.post("/api/auth/register", json={
        "name": SENDER_NAME,
        "email": SENDER_EMAIL,
        "password": SENDER_PASSWORD,
    })
    r = http.post("/api/auth/login", json={
        "email": SENDER_EMAIL,
        "password": SENDER_PASSWORD,
    })
    assert r.status_code == 200, f"sender login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def receiver_token(http):
    """Register + login as receiver, return access_token."""
    http.post("/api/auth/register", json={
        "name": RECEIVER_NAME,
        "email": RECEIVER_EMAIL,
        "password": RECEIVER_PASSWORD,
    })
    r = http.post("/api/auth/login", json={
        "email": RECEIVER_EMAIL,
        "password": RECEIVER_PASSWORD,
    })
    assert r.status_code == 200, f"receiver login failed: {r.text}"
    return r.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
