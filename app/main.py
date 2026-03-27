"""
FortiSIEM Adapter Server

FastAPI application that queries FortiSIEM backend databases directly:
  - PostgreSQL : incidents, CMDB devices, watchlists, lookup tables, context
  - ClickHouse : raw event data

Docs:
  /docs    - Swagger UI
  /redoc   - ReDoc
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.db import clickhouse as ch_db
from app.db import postgres as pg_db
from app.routers import (
    config,
    context,
    devices,
    events,
    health,
    incidents,
    lookup_tables,
    pub_incidents,
    system,
    watchlists,
)

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("fsmapi")


# ------------------------------------------------------------------
# Lifespan: DB pool startup / shutdown
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up – connecting to databases…")

    try:
        await pg_db.create_pool(settings)
        logger.info("PostgreSQL connected")
    except Exception as exc:
        logger.warning("PostgreSQL unavailable at startup (will retry on request): %s", exc)

    try:
        await ch_db.create_client(settings)
        logger.info("ClickHouse connected")
    except Exception as exc:
        logger.warning("ClickHouse unavailable at startup (will retry on request): %s", exc)

    yield

    logger.info("Shutting down – closing database connections…")
    await pg_db.close_pool()
    await ch_db.close_client()


# ------------------------------------------------------------------
# Error logging middleware
# ------------------------------------------------------------------

class AccessLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request and response with body (DEBUG level for 2xx/3xx, ERROR for 4xx+)."""

    # 로그를 남기지 않을 경로 (health check 등 노이즈 제거)
    _SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._SKIP_PATHS:
            return await call_next(request)

        # --- Request body 읽기 (스트림을 소비하므로 재주입 필요) ---
        req_body = await request.body()

        async def _receive():
            return {"type": "http.request", "body": req_body, "more_body": False}

        request = Request(request.scope, receive=_receive)

        # --- Response 실행 및 body 버퍼링 ---
        response = await call_next(request)
        resp_body = b""
        async for chunk in response.body_iterator:
            resp_body += chunk

        # --- 헤더 마스킹 ---
        headers = dict(request.headers)
        if "authorization" in headers:
            headers["authorization"] = headers["authorization"][:15] + "...(masked)"

        log_level = logging.ERROR if response.status_code >= 400 else logging.DEBUG
        logger.log(
            log_level,
            "HTTP %s  %s %s\n"
            "  Client  : %s\n"
            "  Query   : %s\n"
            "  ReqBody : %s\n"
            "  RespBody: %s",
            response.status_code,
            request.method,
            request.url,
            request.client,
            dict(request.query_params),
            req_body.decode("utf-8", errors="replace"),
            resp_body.decode("utf-8", errors="replace"),
        )

        return Response(
            content=resp_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


# ------------------------------------------------------------------
# App
# ------------------------------------------------------------------

app = FastAPI(
    title="FortiSIEM Adapter Server",
    description=(
        "Queries FortiSIEM backend databases (PostgreSQL + ClickHouse) directly. "
        "PostgreSQL: incidents, CMDB, watchlists, lookup tables, context. "
        "ClickHouse: raw event data."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(AccessLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(incidents.router)
app.include_router(events.router)        # prefix: /phoenix/rest/query
app.include_router(pub_incidents.router) # prefix: /phoenix/rest/pub
app.include_router(system.router)        # prefix: /phoenix/rest/system
app.include_router(config.router)        # prefix: /phoenix/rest/config
app.include_router(devices.router)
app.include_router(watchlists.router)
app.include_router(lookup_tables.router)
app.include_router(context.router)
