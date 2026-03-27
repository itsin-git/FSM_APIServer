"""
Event repository – ClickHouse.

FortiSIEM stores raw event data in ClickHouse.
Events are queried directly without the three-step REST API flow.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.repositories.base import ClickHouseRepository

logger = logging.getLogger("fsmapi.repo.event")


class EventRepository(ClickHouseRepository):

    async def search_events(
        self,
        query_string: str,
        select_clause: str = "*",
        time_from_epoch: Optional[int] = None,
        time_to_epoch: Optional[int] = None,
        start: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        # TODO: Build and execute ClickHouse query
        # Hint: main event table is likely `events_all` or `event` in the default database
        # Example:
        #   SELECT {select_clause}
        #   FROM events_all
        #   WHERE {query_string}
        #     AND receiveTime BETWEEN {time_from_epoch} AND {time_to_epoch}
        #   ORDER BY receiveTime DESC
        #   LIMIT {limit} OFFSET {start}
        raise NotImplementedError("TODO: implement search_events ClickHouse query")

    async def get_event_by_id(
        self,
        event_id: str,
        select_clause: str = "*",
        time_from_epoch: Optional[int] = None,
        time_to_epoch: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        # TODO: SELECT {select_clause} FROM events_all
        #        WHERE eventId = {event_id}
        #          AND receiveTime BETWEEN ...
        #        LIMIT 1
        raise NotImplementedError("TODO: implement get_event_by_id ClickHouse query")

    async def get_events_by_incident(
        self,
        incident_id: int,
        time_from_epoch: Optional[int] = None,
        time_to_epoch: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        # TODO: SELECT * FROM events_all
        #        WHERE phIncidentId = {incident_id}
        #          AND receiveTime BETWEEN ...
        #        ORDER BY receiveTime DESC
        #        LIMIT {limit}
        raise NotImplementedError("TODO: implement get_events_by_incident ClickHouse query")

    async def run_raw_query(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        # TODO: Direct passthrough for arbitrary ClickHouse SQL
        # Used by the /events/query endpoint when sql_query is provided
        raise NotImplementedError("TODO: implement run_raw_query ClickHouse execution")

    async def count_events(
        self,
        query_string: str,
        time_from_epoch: Optional[int] = None,
        time_to_epoch: Optional[int] = None,
    ) -> int:
        # TODO: SELECT count() FROM events_all WHERE ...
        raise NotImplementedError("TODO: implement count_events ClickHouse query")

    async def get_events_by_ids(
        self,
        event_ids: List[int],
        time_from_epoch_s: Optional[int] = None,
        time_to_epoch_s: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch full event rows from ClickHouse by event ID list.
        DB: fsiem  Table: events_all
        Key columns: eventId (UInt64), phCustId, phRecvTime (DateTime), eventType, rawEventMsg

        time_from_epoch_s / time_to_epoch_s: Unix epoch seconds.
        toDateTime() is used so ClickHouse handles server timezone correctly.
        """
        if not event_ids:
            return []
        ids_csv = ", ".join(str(i) for i in event_ids)
        conditions = [f"eventId IN ({ids_csv})"]
        if time_from_epoch_s is not None:
            conditions.append(f"phRecvTime >= toDateTime({time_from_epoch_s})")
        if time_to_epoch_s is not None:
            conditions.append(f"phRecvTime <= toDateTime({time_to_epoch_s})")
        sql = f"SELECT * FROM events_all WHERE {' AND '.join(conditions)}"
        logger.debug("get_events_by_ids SQL: %s", sql)
        return await self.query(sql)
