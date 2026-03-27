"""
Event service.

Delegates all DB access to EventRepository (ClickHouse).
The REST three-step flow (submit/progress/result) is replaced by
direct ClickHouse queries; the endpoint contract is kept the same
so existing callers don't need to change.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.repositories.event import EventRepository
from app.schemas.event import EventQueryRequest, SearchEventsRequest
from app.services.time_utils import build_time_xml, to_epoch

logger = logging.getLogger("fsmapi.service.event")


class EventService:
    def __init__(self, repo: EventRepository):
        self._repo = repo

    async def submit_query(self, req: EventQueryRequest) -> str:
        """
        In the DB-direct model there is no async query submission.
        We execute immediately and return a synthetic query_id (UUID)
        that the caller can pass to get_results() within the same session.

        For backward compatibility the three endpoints still exist, but
        progress is always 100% once submit_query returns.
        """
        time_from = to_epoch(req.time_from) if req.time_from else None
        time_to = to_epoch(req.time_to) if req.time_to else None

        if req.sql_query:
            rows = await self._repo.run_raw_query(req.sql_query)
        else:
            rows = await self._repo.search_events(
                query_string=req.conditions or "1=1",
                select_clause=req.attr_list or "*",
                time_from_epoch=time_from,
                time_to_epoch=time_to,
            )

        # Cache result under a synthetic query_id so get_results() can retrieve it.
        # TODO: replace in-memory dict with Redis or a proper cache when scaling out.
        query_id = str(uuid.uuid4())
        _query_cache[query_id] = rows
        return query_id

    async def get_progress(self, query_id: str) -> Dict[str, Any]:
        """Always 100% – DB queries are synchronous from the caller's perspective."""
        in_cache = query_id in _query_cache
        return {
            "query_id": query_id,
            "progress_pct": "100" if in_cache else "0",
        }

    async def get_results(
        self, query_id: str, start: int = 0, per_page: int = 50
    ) -> Dict[str, Any]:
        rows = _query_cache.get(query_id, [])
        page = rows[start: start + per_page]
        return {
            "queryId": query_id,
            "totalCount": len(rows),
            "start": start,
            "events": page,
        }

    async def search_events(self, req: SearchEventsRequest) -> Dict[str, Any]:
        """One-shot search: query ClickHouse directly and return results."""
        time_from = to_epoch(req.time_from) if req.time_from else None
        time_to = to_epoch(req.time_to) if req.time_to else None

        rows = await self._repo.search_events(
            query_string=req.query_string,
            select_clause=req.select_clause or "*",
            time_from_epoch=time_from,
            time_to_epoch=time_to,
            start=req.start,
            limit=req.per_page,
        )
        return {
            "queryId": None,
            "totalCount": len(rows),
            "start": req.start,
            "events": rows,
        }

    async def get_event_by_id(
        self,
        event_id: str,
        select_clause: str = "",
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
    ) -> Any:
        tf = to_epoch(time_from) if time_from else None
        tt = to_epoch(time_to) if time_to else None
        return await self._repo.get_event_by_id(
            event_id=event_id,
            select_clause=select_clause or "*",
            time_from_epoch=tf,
            time_to_epoch=tt,
        )


# ---------------------------------------------------------------------------
# In-process query cache (submit_query → get_results)
# TODO: replace with Redis for multi-worker deployments
# ---------------------------------------------------------------------------
_query_cache: Dict[str, List[Dict[str, Any]]] = {}
