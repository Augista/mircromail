import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Must be set before importing any auth-service module (config.py reads these at import time)
os.environ.setdefault("AUTH_DB_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-32chars")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRATION_HOURS", "24")
os.environ.setdefault("JWT_REFRESH_EXPIRATION_DAYS", "30")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import PasswordManager  # noqa: E402 (needs sys.path set first)

TEST_USER_EMAIL = "test@example.com"
TEST_USER_NAME = "Test User"
TEST_USER_PASSWORD = "securepassword123"


def make_mock_user(
    user_id=None,
    email=TEST_USER_EMAIL,
    name=TEST_USER_NAME,
    password=TEST_USER_PASSWORD,
):
    """Create a mock User object with all required attributes populated."""
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = email
    user.name = name
    user.password_hash = PasswordManager.hash_password(password)
    user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return user


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.refresh = MagicMock()
    db.close = MagicMock()
    return db


@pytest.fixture
def client():
    from main import app
    return TestClient(app)
