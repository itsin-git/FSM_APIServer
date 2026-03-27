# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (with auto-reload)
uvicorn app.main:app --reload

# Run on specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run all tests
pytest -v

# Run a single test file
pytest tests/test_incidents.py -v

# Run a single test
pytest tests/test_incidents.py::test_list_incidents -v
```

## Architecture

This is a FastAPI adapter server (v2.0.0) bridging a **FortiSOAR connector** to a **FortiSIEM** backend. Rather than using FortiSIEM's HTTP REST API, it queries FortiSIEM's backend databases directly for performance.

```
FortiSOAR Connector → This Adapter (FastAPI) → FortiSIEM PostgreSQL + ClickHouse
```

### Layer Structure

```
app/routers/        → HTTP endpoint handlers
app/services/       → Business logic orchestration
app/repositories/   → Raw database query execution
app/db/             → Connection pool/client managers (asyncpg + clickhouse-connect)
app/core/           → Config, auth, exceptions
app/schemas/        → Pydantic request/response models
app/dependencies.py → FastAPI DI wiring (pool → repo → service)
app/client/         → HTTP client for FortiSIEM REST API (exists but unused; direct DB preferred)
app/queue/          → Redis/RQ job queue (redis_client.py + jobs.py for background event processing)
app/worker.py       → RQ worker entry point (run separately for background jobs)
app/xml_templates/  → XML payload templates for FortiSIEM report queries
app/services/time_utils.py → ISO-8601 ↔ epoch conversions and XML time element generation
```

### Router Prefixes

| Router file | Prefix | Notes |
|---|---|---|
| `routers/incidents.py` | `/api/v1` | Incident CRUD |
| `routers/events.py` | `/phoenix/rest/query` | Matches FortiSIEM 7.4.2 OpenAPI spec exactly |
| `routers/pub_incidents.py` | `/phoenix/rest/pub` | GET/POST `/incident` |
| `routers/system.py` | `/phoenix/rest/system` | Returns static health summary |
| `routers/config.py` | `/phoenix/rest/config` | GET `/Domain` — returns XML |
| `routers/devices.py` | `/api/v1` | CMDB devices |
| `routers/watchlists.py` | `/api/v1` | Watchlist CRUD |
| `routers/lookup_tables.py` | `/api/v1` | Lookup table CRUD |
| `routers/context.py` | `/api/v1` | IP/host/user context |
| `routers/health.py` | _(none)_ | GET `/health` |

### Database Split

- **PostgreSQL** (`asyncpg` pool): incidents, CMDB devices, watchlists, lookup tables, context enrichment
- **ClickHouse** (`clickhouse-connect` async client): raw event data and time-series queries

Known PostgreSQL tables (confirmed from implemented queries):
- `ph_incident` — incident records; `ph_sys_domain` — org/domain names; `ph_drq_rule` — detection rules
- `ph_incident_detail` — per-incident details including `trigger_events` XML (used to extract event IDs for ClickHouse lookups)

### Event Query Flow (3-step async simulation)

The events API mimics FortiSIEM's async query pattern, but executes synchronously internally:
1. `POST /phoenix/rest/query/eventQuery` — executes query immediately, caches results in-memory (`_query_cache`), returns a synthetic `queryId`
2. `GET /phoenix/rest/query/progress/{queryId}` — always returns 100%
3. `GET /phoenix/rest/query/events/{queryId}/{offset}/{limit}` — returns paginated results from cache

The request body for step 1 accepts either `text/xml` (raw XML, as sent by the FortiSOAR connector) or `application/json` (`EventQueryRequest`). There is also a `/phoenix/rest/query/archive` endpoint (same logic, intended for archive storage) and convenience extras `/phoenix/rest/query/search` and `/phoenix/rest/query/by-id/{eventId}`.

The `_query_cache` dict lives in `app/services/event.py` and is **process-local** — only safe for single-worker deployments. A TODO exists to replace it with Redis for multi-worker scaling.

### Authentication

All endpoints use HTTP Basic Auth in FortiSIEM format: `org/username:password`.
Example: `super/admin:changeme` → `Authorization: Basic c3VwZXIvYWRtaW46Y2hhbmdlbWU=`

In tests, set the header directly: `{"Authorization": "Basic c3VwZXIvYWRtaW46Y2hhbmdlbWU="}` (base64 of `super/admin:changeme`).

### Configuration

Copy `.env.example` to `.env` and configure:
- `POSTGRES_*` — connection to FortiSIEM's `phoenixdb` PostgreSQL database
- `CLICKHOUSE_*` — connection to FortiSIEM's ClickHouse instance
- `REDIS_*` — Redis connection for the RQ job queue (host, port, db, password, queue name)
- `API_ORG` / `API_USERNAME` / `API_PASSWORD` — credentials the adapter accepts (FortiSIEM format)

### Incident Enrichment

`IncidentService` heavily transforms raw DB rows before returning responses:
- `incidentStatus` integer codes → human-readable strings (via `INCIDENT_STATUS` dict): `0=Active, 1=Auto Cleared, 2=Manually Cleared, 3=System Cleared`
- `incidentCategory` integers: `1=Availability, 2=Performance, 3=Change, 4=Security, 5=Other`
- `incidentSrc` / `incidentTarget` CSV strings (e.g., `"srcIp:1.2.3.4,srcName:host1"`) → parsed into dicts
- Attack technique fields stored as JSON strings → parsed into structured objects
- Rule XML from `ph_drq_rule` → extracted `eventName`, `eventType`, and MITRE technique ID/name mappings

### Response Field Aliasing

Event response schemas use camelCase aliases via Pydantic `Field(alias=...)` with `populate_by_name=True`. For example, `EventResultResponse.total_count` serializes as `totalCount`. When constructing these models, pass values by the Python field name (snake_case).

### Implementation Status

The service and router layers are complete. `IncidentRepository.list_pub_incidents` has a full SQL implementation. All other repository methods in `app/repositories/` raise `NotImplementedError("TODO: implement...")` with SQL hints — these are the primary remaining work. `IncidentService.get_associated_events()` also raises `NotImplementedError` (requires `EventRepository` to be injected into the service).

### Testing Pattern

Tests mock repositories using `AsyncMock` and override FastAPI dependencies:
```python
incident_repo = AsyncMock()
app.dependency_overrides[get_incident_service] = lambda: IncidentService(incident_repo)
```

API docs available at `/docs` (Swagger UI) and `/redoc` when the server is running.
