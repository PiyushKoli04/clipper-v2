"""Tests for FastAPI backend routes and logic."""

import pytest
from fastapi.testclient import TestClient
from server.app import app
from server.auth import get_current_user

# Override dependency for testing
app.dependency_overrides[get_current_user] = lambda: {"email": "test@example.com", "uid": "test-uid"}

client = TestClient(app)


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "app": "clipper-v2"}


def test_public_config():
    resp = client.get("/api/public-config")
    assert resp.status_code == 200
    assert "firebase" in resp.json()


def test_spa_serving():
    # If dist/ exists, check that GET / returns index.html
    from server.app import FRONTEND_DIST
    if FRONTEND_DIST.exists():
        resp = client.get("/")
        assert resp.status_code == 200
        assert "html" in resp.text.lower()


