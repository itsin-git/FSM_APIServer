"""
FastAPI dependency injection.

Services receive Repository objects; repositories receive DB connections.
DB pools are initialized at startup (see main.py lifespan) and retrieved here.
"""

from __future__ import annotations

import asyncpg
from clickhouse_connect.driver.asyncclient import AsyncClient
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.db import clickhouse as ch_db
from app.db import postgres as pg_db

# Repositories
from app.repositories.context import ContextRepository
from app.repositories.device import DeviceRepository
from app.repositories.domain import DomainRepository
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.lookup_table import LookupTableRepository
from app.repositories.watchlist import WatchlistRepository

# Services
from app.services.context import ContextService
from app.services.device import DeviceService
from app.services.domain import DomainService
from app.services.event import EventService
from app.services.health import HealthService
from app.services.incident import IncidentService, TriggeringEventsService
from app.services.lookup_table import LookupTableService
from app.services.watchlist import WatchlistService


# ------------------------------------------------------------------
# DB connection providers
# ------------------------------------------------------------------

def get_pg_pool() -> asyncpg.Pool:
    return pg_db.get_pool()


def get_ch_client() -> AsyncClient:
    return ch_db.get_client()


# ------------------------------------------------------------------
# Repository providers
# ------------------------------------------------------------------

def get_incident_repo(pool: asyncpg.Pool = Depends(get_pg_pool)) -> IncidentRepository:
    return IncidentRepository(pool)


def get_event_repo(client: AsyncClient = Depends(get_ch_client)) -> EventRepository:
    return EventRepository(client)


def get_device_repo(pool: asyncpg.Pool = Depends(get_pg_pool)) -> DeviceRepository:
    return DeviceRepository(pool)


def get_watchlist_repo(pool: asyncpg.Pool = Depends(get_pg_pool)) -> WatchlistRepository:
    return WatchlistRepository(pool)


def get_lookup_table_repo(pool: asyncpg.Pool = Depends(get_pg_pool)) -> LookupTableRepository:
    return LookupTableRepository(pool)


def get_context_repo(pool: asyncpg.Pool = Depends(get_pg_pool)) -> ContextRepository:
    return ContextRepository(pool)


def get_domain_repo(pool: asyncpg.Pool = Depends(get_pg_pool)) -> DomainRepository:
    return DomainRepository(pool)


# ------------------------------------------------------------------
# Service providers
# ------------------------------------------------------------------

def get_health_service(
    pool: asyncpg.Pool = Depends(get_pg_pool),
    client: AsyncClient = Depends(get_ch_client),
) -> HealthService:
    return HealthService(pool, client)


def get_incident_service(repo: IncidentRepository = Depends(get_incident_repo)) -> IncidentService:
    return IncidentService(repo)


def get_event_service(repo: EventRepository = Depends(get_event_repo)) -> EventService:
    return EventService(repo)


def get_device_service(repo: DeviceRepository = Depends(get_device_repo)) -> DeviceService:
    return DeviceService(repo)


def get_watchlist_service(repo: WatchlistRepository = Depends(get_watchlist_repo)) -> WatchlistService:
    return WatchlistService(repo)


def get_lookup_table_service(repo: LookupTableRepository = Depends(get_lookup_table_repo)) -> LookupTableService:
    return LookupTableService(repo)


def get_context_service(repo: ContextRepository = Depends(get_context_repo)) -> ContextService:
    return ContextService(repo)


def get_domain_service(repo: DomainRepository = Depends(get_domain_repo)) -> DomainService:
    return DomainService(repo)


def get_triggering_events_service() -> TriggeringEventsService:
    from app.queue.redis_client import get_redis
    return TriggeringEventsService(get_redis())
