"""
Incident repository – PostgreSQL.

FortiSIEM stores incident records in PostgreSQL.
Table names and column mappings need to be confirmed
against the actual FortiSIEM DB schema.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from app.repositories.base import PostgresRepository

logger = logging.getLogger("fsmapi.repo.incident")


class IncidentRepository(PostgresRepository):

    async def list_incidents(
        self,
        filters: Dict[str, Any],
        start: int = 0,
        size: int = 500,
        time_from_ms: Optional[int] = None,
        time_to_ms: Optional[int] = None,
        order_field: str = "incidentLastSeen",
        descending: bool = True,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        # TODO: Write SELECT query against FortiSIEM incident table
        # Hint: table is likely `phoenix_attribute` or `ph_incident` in phoenixdb
        # Filter columns: incidentStatus, phIncidentCategory, eventSeverityCat, eventType, etc.
        # Example structure:
        #   SELECT <fields> FROM <incident_table>
        #   WHERE incidentStatus = ANY($1)
        #     AND incidentLastSeen BETWEEN $2 AND $3
        #   ORDER BY <order_field> DESC
        #   LIMIT $4 OFFSET $5
        raise NotImplementedError("TODO: implement list_incidents SQL query")

    async def get_by_ids(
        self,
        incident_ids: List[int],
        time_from_ms: Optional[int] = None,
        time_to_ms: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        # TODO: SELECT * FROM <incident_table> WHERE incidentId = ANY($1)
        raise NotImplementedError("TODO: implement get_by_ids SQL query")

    async def update_incident(
        self,
        incident_id: int,
        status: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> bool:
        # TODO: UPDATE <incident_table>
        #        SET incidentStatus = $2, resolution = $3
        #        WHERE incidentId = $1
        raise NotImplementedError("TODO: implement update_incident SQL query")

    async def add_comment(self, incident_id: int, comment: str) -> bool:
        # TODO: INSERT INTO <incident_comment_table> (incidentId, comment, createdAt)
        #        VALUES ($1, $2, NOW())
        raise NotImplementedError("TODO: implement add_comment SQL query")

    async def clear_incident(self, incident_id: int, comment: str) -> bool:
        # TODO: UPDATE <incident_table>
        #        SET incidentStatus = 2, clearComment = $2
        #        WHERE incidentId = $1
        raise NotImplementedError("TODO: implement clear_incident SQL query")

    # Mapping from API field name → SQL column (whitelisted to prevent injection)
    _PUB_ORDER_BY_MAP: Dict[str, str] = {
        "incidentLastSeen":  "i.last_seen_time",
        "incidentFirstSeen": "i.first_seen_time",
        "incidentId":        "i.inst_incident_id",
        "eventSeverity":     "i.severity",
        "incidentStatus":    "i.incident_status",
        "incidentReso":      "i.incident_reso",
        "customer":          "d.name",
    }

    async def list_pub_incidents(
        self,
        time_from_ms: Optional[int],
        time_to_ms: Optional[int],
        size: int = 100,
        start: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "incidentLastSeen",
        descending: bool = True,
    ) -> List[Dict[str, Any]]:
        params: List[Any] = []
        conditions: List[str] = []

        def _p(value: Any) -> str:
            params.append(value)
            return f"${len(params)}"

        if time_from_ms is not None and time_to_ms is not None:
            conditions.append(f"i.last_seen_time BETWEEN {_p(time_from_ms)} AND {_p(time_to_ms)}")

        # Dynamic filter conditions (all parameterized, columns whitelisted)
        _filter_cols: Dict[str, str] = {
            "incidentId":           "i.inst_incident_id",
            "incidentStatus":       "i.incident_status",
            "status":               "i.incident_status",   # connector alias
            "eventSeverity":        "i.severity",
            "eventSeverityCat":     "i.severity_cat",
            "phIncidentCategory":   "r.category",
            "phSubIncidentCategory":"i.ph_incident_category",
            "phCustId":             "i.inst_incident_cust_id",
            "customer":             "d.name",
            "incidentReso":         "i.incident_reso",
            # eventType: rule_xml 파싱 결과라 SQL 직접 필터 불가 → 무시
        }
        if filters:
            for key, col in _filter_cols.items():
                values = filters.get(key)
                if values:
                    conditions.append(f"{col} = ANY({_p(values)})")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        order_col = self._PUB_ORDER_BY_MAP.get(order_by, "i.last_seen_time")
        direction = "DESC" if descending else "ASC"

        sql = f"""
            SELECT
                i.incident_count,
                i.inst_incident_id,
                i.incident_src,
                i.tactics,
                i.incident_reso,
                i.severity,
                i.orig_device_ip::text AS orig_device_ip,
                i.incident_title,
                i.incident_detail_json,
                i.incident_status,
                i.incident_target,
                i.techniques,
                i.tag_name,
                i.severity_cat,
                i.last_seen_time,
                i.first_seen_time,
                i.orig_device_name,
                i.cleared_time,
                i.ph_incident_category,
                d.name AS customer,
                r.rule_xml,
                r.category AS rule_category
            FROM ph_incident i
            LEFT JOIN ph_sys_domain d ON i.inst_incident_cust_id = d.domain_id
            LEFT JOIN ph_drq_rule r ON i.rule_id = r.id
            {where}
            ORDER BY {order_col} {direction}
            LIMIT {_p(size)} OFFSET {_p(start)}
        """
        return await self.fetch(sql, *params)

    async def get_trigger_event_ids(
        self,
        incident_id: int,
        size: int = 100,
    ) -> Dict[str, Any]:
        """
        Query ph_incident_detail for trigger_events XML and extract event IDs,
        along with the time window for ClickHouse:
          time_from_epoch_s = creation_time(ms) / 1000 - 300  (5 min before)
          time_to_epoch_s   = last_modified_time(ms) / 1000 + 300  (5 min after)

        Returns:
          {
            "event_ids": List[int],
            "time_from_epoch_s": int | None,
            "time_to_epoch_s":   int | None,
          }
        """
        rows = await self.fetch(
            "SELECT trigger_events, creation_time, last_modified_time"
            " FROM ph_incident_detail WHERE incident_id = $1",
            incident_id,
        )
        event_ids: List[int] = []
        time_from_epoch_s: Optional[int] = None
        time_to_epoch_s: Optional[int] = None

        for row in rows:
            # Compute time window from the first row that has timing info
            if time_from_epoch_s is None:
                ct = row.get("creation_time")
                lm = row.get("last_modified_time")
                if ct is not None:
                    time_from_epoch_s = int(ct) // 1000 - 300
                if lm is not None:
                    time_to_epoch_s = int(lm) // 1000 + 300

            if len(event_ids) >= size:
                continue
            xml_str = row.get("trigger_events") or ""
            if not xml_str:
                continue
            try:
                root = ET.fromstring(xml_str)
                for el in root.findall("triggerEvents"):
                    for id_str in (el.text or "").split(","):
                        id_str = id_str.strip()
                        if id_str:
                            try:
                                event_ids.append(int(id_str))
                            except ValueError:
                                pass
                        if len(event_ids) >= size:
                            break
                    if len(event_ids) >= size:
                        break
            except ET.ParseError as exc:
                logger.debug("trigger_events XML parse error for incident %s: %s", incident_id, exc)

        return {
            "event_ids": event_ids[:size],
            "time_from_epoch_s": time_from_epoch_s,
            "time_to_epoch_s": time_to_epoch_s,
        }
