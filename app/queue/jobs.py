"""
rq job functions executed by worker subprocesses.

Each function is a synchronous entry point that wraps async DB logic via asyncio.run().
Workers run these in separate processes, so DB connections are created fresh per job.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger("fsmapi.worker.jobs")


async def _fetch_triggering_events(
    incident_id: int,
    size: int,
) -> List[Dict[str, Any]]:
    """Async core: query PostgreSQL then ClickHouse, return serializable event list."""
    import asyncpg
    import clickhouse_connect

    from app.core.config import get_settings
    from app.repositories.event import EventRepository
    from app.repositories.incident import IncidentRepository
    from app.services.incident import _build_triggering_event

    s = get_settings()

    # Create fresh DB connections for this worker process
    pool = await asyncpg.create_pool(
        dsn=s.postgres_dsn,
        min_size=1,
        max_size=3,
        ssl=s.postgres_ssl or None,
    )
    ch_client = await clickhouse_connect.get_async_client(
        host=s.clickhouse_host,
        port=s.clickhouse_port,
        database=s.clickhouse_db,
        username=s.clickhouse_user,
        password=s.clickhouse_password,
        secure=s.clickhouse_secure,
    )

    try:
        incident_repo = IncidentRepository(pool)
        event_repo = EventRepository(ch_client)

        trigger_info = await incident_repo.get_trigger_event_ids(incident_id, size)
        event_ids = trigger_info["event_ids"]
        time_from_s = trigger_info["time_from_epoch_s"]
        time_to_s = trigger_info["time_to_epoch_s"]

        logger.debug(
            "incident=%s event_ids=%s time=%s~%s",
            incident_id, event_ids, time_from_s, time_to_s,
        )

        raw_rows = await event_repo.get_events_by_ids(
            event_ids=event_ids,
            time_from_epoch_s=time_from_s,
            time_to_epoch_s=time_to_s,
        )

        logger.debug("clickhouse returned %d rows for incident=%s", len(raw_rows), incident_id)
        return [_build_triggering_event(row, idx) for idx, row in enumerate(raw_rows)]

    finally:
        await pool.close()
        ch_client.close()  # clickhouse-connect close() is synchronous


def process_triggering_events(incident_id: int, size: int) -> List[Dict[str, Any]]:
    """
    rq job entry point (synchronous).

    Called by a worker subprocess; wraps async DB logic with asyncio.run().
    Result is stored in Redis by rq and retrieved via Job.result.
    """
    logger.info("job start: incident_id=%s size=%s", incident_id, size)
    result = asyncio.run(_fetch_triggering_events(incident_id, size))
    logger.info("job done: incident_id=%s rows=%d", incident_id, len(result))
    return result
