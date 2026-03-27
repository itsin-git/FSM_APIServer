"""
Tests for the incident router and service layer.
Uses mocked IncidentRepository – no real DB required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_incident_service, get_health_service
from app.main import app
from app.services.incident import IncidentService
from app.services.health import HealthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_incident_svc(repo_mock):
    return IncidentService(repo_mock)


@pytest.fixture
def incident_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def test_app(incident_repo):
    # Bypass lifespan DB connections for unit tests
    app.dependency_overrides[get_incident_service] = lambda: _make_incident_svc(incident_repo)
    # Stub health so /health doesn't need real DB
    stub_health = AsyncMock(spec=HealthService)
    stub_health.check = AsyncMock(return_value={"status": "ok", "postgres": {"ok": True, "detail": "connected"}, "clickhouse": {"ok": True, "detail": "connected"}})
    app.dependency_overrides[get_health_service] = lambda: stub_health
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    c = TestClient(test_app, raise_server_exceptions=False)
    c.headers.update({"Authorization": "Basic c3VwZXIvYWRtaW46Y2hhbmdlbWU="})  # admin:changeme
    return c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_list_incidents_success(client, incident_repo):
    """POST /api/v1/incidents returns enriched incident list."""
    incident_repo.list_incidents = AsyncMock(return_value=[
        {
            "incidentId": 1001,
            "incidentStatus": 0,
            "eventSeverityCat": "HIGH",
            "incidentSrc": "srcIp:1.2.3.4,srcName:host1,",
        }
    ])

    resp = client.post(
        "/api/v1/incidents",
        json={"size": 10, "incidentStatus": ["Active"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    incident = data["data"][0]
    assert incident["incidentId"] == 1001
    assert incident["incidentStatusStr"] == "active"
    assert isinstance(incident["incidentSrc"], dict)
    assert incident["incidentSrc"]["srcIp"] == "1.2.3.4"


def test_list_incidents_repo_error(client, incident_repo):
    """Repository NotImplementedError → 500."""
    incident_repo.list_incidents = AsyncMock(side_effect=NotImplementedError("TODO"))
    resp = client.post("/api/v1/incidents", json={})
    assert resp.status_code == 500


def test_update_incident_success(client, incident_repo):
    """PUT /api/v1/incidents → success message."""
    incident_repo.update_incident = AsyncMock(return_value=True)

    resp = client.put(
        "/api/v1/incidents",
        json={"incidentId": 999, "incidentStatus": "Manually Cleared"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "Incident updated"
    assert str(body["incident_id"]) == "999"


def test_update_incident_not_found(client, incident_repo):
    """PUT /api/v1/incidents → not found message when repo returns False."""
    incident_repo.update_incident = AsyncMock(return_value=False)

    resp = client.put(
        "/api/v1/incidents",
        json={"incidentId": 404, "incidentStatus": "Active"},
    )
    assert resp.status_code == 200
    assert "does not exist" in resp.json()["message"]


def test_comment_incident(client, incident_repo):
    """POST /api/v1/incidents/comment → success."""
    incident_repo.add_comment = AsyncMock(return_value=True)
    resp = client.post(
        "/api/v1/incidents/comment",
        json={"id": 42, "comment_text": "Investigated."},
    )
    assert resp.status_code == 200
    assert "comment" in resp.json()["message"].lower()


def test_clear_incident(client, incident_repo):
    """POST /api/v1/incidents/clear → success."""
    incident_repo.clear_incident = AsyncMock(return_value=True)
    resp = client.post(
        "/api/v1/incidents/clear",
        json={"id": 77, "comment_text": "False positive"},
    )
    assert resp.status_code == 200
    assert "cleared" in resp.json()["message"].lower()


def test_health_endpoint(client):
    """GET /health returns ok status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "postgres" in body
    assert "clickhouse" in body
