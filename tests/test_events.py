"""
Tests for the event router and service layer.
Uses mocked EventRepository – no real ClickHouse required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_event_service, get_health_service
from app.main import app
from app.services.event import EventService, _query_cache
from app.services.health import HealthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_event_svc(repo_mock):
    return EventService(repo_mock)


@pytest.fixture(autouse=True)
def clear_query_cache():
    """Ensure the in-process cache is clean between tests."""
    _query_cache.clear()
    yield
    _query_cache.clear()


@pytest.fixture
def event_repo():
    return AsyncMock()


@pytest.fixture
def test_app(event_repo):
    stub_health = AsyncMock(spec=HealthService)
    stub_health.check = AsyncMock(return_value={
        "status": "ok",
        "postgres": {"ok": True, "detail": "connected"},
        "clickhouse": {"ok": True, "detail": "connected"},
    })
    app.dependency_overrides[get_event_service] = lambda: _make_event_svc(event_repo)
    app.dependency_overrides[get_health_service] = lambda: stub_health
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    c = TestClient(test_app, raise_server_exceptions=False)
    c.headers.update({"Authorization": "Basic c3VwZXIvYWRtaW46Y2hhbmdlbWU="})  # admin:changeme
    return c


# ---------------------------------------------------------------------------
# submit_query → get_progress → get_results flow
# ---------------------------------------------------------------------------

def test_submit_query_conditions(client, event_repo):
    """POST /api/v1/events/query submits and caches results; returns query_id."""
    event_repo.search_events = AsyncMock(return_value=[
        {"eventId": "abc", "eventName": "TestEvent"}
    ])

    resp = client.post(
        "/phoenix/rest/query/eventQuery",
        json={"conditions": "phEventCategory = 1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "query_id" in body
    assert len(body["query_id"]) == 36  # UUID


def test_submit_query_sql(client, event_repo):
    """POST /api/v1/events/query with sql_query calls run_raw_query."""
    event_repo.run_raw_query = AsyncMock(return_value=[{"count": 42}])

    resp = client.post(
        "/phoenix/rest/query/eventQuery",
        json={"sql_query": "SELECT count() FROM ph_event"},
    )
    assert resp.status_code == 200
    query_id = resp.json()["query_id"]
    event_repo.run_raw_query.assert_called_once()

    # Progress should be 100% immediately
    prog = client.get(f"/phoenix/rest/query/progress/{query_id}")
    assert prog.json()["progress_pct"] == "100"

    # Results  — spec path: /events/{queryId}/{offset}/{limit}
    results = client.get(f"/phoenix/rest/query/events/{query_id}/0/50")
    assert results.status_code == 200
    body = results.json()
    # EventResultResponse serializes with snake_case field names
    total = body.get("totalCount") or body.get("total_count")
    assert total == 1
    assert body["events"][0]["count"] == 42


def test_get_progress_unknown_query(client):
    """GET /api/v1/events/progress/unknown → progress_pct=0."""
    resp = client.get("/phoenix/rest/query/progress/nonexistent-id")
    assert resp.status_code == 200
    assert resp.json()["progress_pct"] == "0"


def test_get_results_empty_cache(client):
    """GET /api/v1/events/results/missing → empty events list."""
    resp = client.get("/phoenix/rest/query/events/missing-id/0/50")
    assert resp.status_code == 200
    body = resp.json()
    assert body["events"] == []
    total = body.get("totalCount") or body.get("total_count", 0)
    assert total == 0


# ---------------------------------------------------------------------------
# search_events (one-shot)
# ---------------------------------------------------------------------------

def test_search_events(client, event_repo):
    """POST /api/v1/events/search returns events directly."""
    event_repo.search_events = AsyncMock(return_value=[
        {"srcIpAddr": "10.0.0.1", "eventName": "Login"}
    ])

    resp = client.post(
        "/phoenix/rest/query/search",
        json={"query_string": 'srcIpAddr = "10.0.0.1"', "rel_time": "Hours", "value": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["totalCount"] == 1
    assert body["events"][0]["srcIpAddr"] == "10.0.0.1"


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------

def test_parse_query_id_plain():
    from app.client.fortisiem import parse_query_id
    assert parse_query_id("12345,1700000000") == "12345,1700000000"


def test_parse_query_id_xml():
    from app.client.fortisiem import parse_query_id
    xml = (
        '<?xml version="1.0"?>'
        '<response requestId="12345">'
        '<result><expireTime>1700000000</expireTime></result>'
        '</response>'
    )
    assert parse_query_id(xml) == "12345,1700000000"


def test_build_time_xml_relative():
    from app.services.time_utils import build_time_xml
    assert 'val="120"' in build_time_xml(rel_time="Hours", value=2)


def test_build_time_xml_absolute():
    from app.services.time_utils import build_time_xml
    result = build_time_xml(
        time_from="2024-01-01T00:00:00.000Z",
        time_to="2024-01-02T00:00:00.000Z",
    )
    assert "<Low>" in result and "<High>" in result


def test_build_time_xml_default():
    from app.services.time_utils import build_time_xml
    assert 'val="120"' in build_time_xml()
