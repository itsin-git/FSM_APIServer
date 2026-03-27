"""
Incident service.

Orchestrates business logic; delegates all DB access to IncidentRepository.
"""

from __future__ import annotations

import json
import logging
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.repositories.incident import IncidentRepository
from app.schemas.incident import (
    ClearIncidentRequest,
    CommentIncidentRequest,
    IncidentDetailRequest,
    IncidentListRequest,
    UpdateIncidentRequest,
)
from app.services.time_utils import to_milliseconds

logger = logging.getLogger("fsmapi.service.incident")

PARAMS_MAPPING: Dict[str, str] = {
    "Active": "0",
    "Auto Cleared": "1",
    "Manually Cleared": "2",
    "System Cleared": "3",
    "True Positive": "2",
    "False Positive": "3",
}
INCIDENT_CATEGORY_MAPPING: Dict[str, int] = {
    "Availability": 1, "Performance": 2, "Change": 3, "Security": 4, "Other": 5,
}
INCIDENT_STATUS: Dict[int, str] = {
    0: "active", 1: "automatically cleared", 2: "manually cleared", 3: "system cleared",
}
PUB_INCIDENT_STATUS_STR: Dict[int, str] = {
    0: "active", 1: "Auto Cleared", 2: "Manual Cleared", 3: "System Cleared",
}


def _parse_kv_csv(raw: Optional[str]) -> Dict[str, str]:
    """Parse FortiSIEM CSV key:value field, e.g. 'srcIpAddr:1.2.3.4,srcPort:80'."""
    if not raw:
        return {}
    result: Dict[str, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" in pair:
            idx = pair.index(":")
            result[pair[:idx].strip()] = pair[idx + 1:].strip()
    return result


def _parse_rule_xml(rule_xml: Optional[str]) -> Dict[str, Any]:
    """Extract eventName, eventType, and technique name map from rule_xml."""
    out: Dict[str, Any] = {"event_name": "", "event_type": "", "technique_names": {}}
    if not rule_xml:
        return out
    try:
        root = ET.fromstring(rule_xml.strip())
        name_el = root.find("Name")
        if name_el is not None and name_el.text:
            out["event_name"] = name_el.text.strip()
        inc_def = root.find("IncidentDef")
        if inc_def is not None:
            out["event_type"] = inc_def.get("eventType", "")
        # Build technique ID → name mapping from DataRequest attributes
        tech_ids = [t.strip() for t in root.get("technique", "").split(",") if t.strip()]
        tech_names = [n.strip() for n in root.get("techniqueName", "").split(",") if n.strip()]
        out["technique_names"] = dict(zip(tech_ids, tech_names))
    except Exception as exc:
        logger.debug("rule_xml parse error: %s", exc)
    return out


def _build_attack_technique(techniques_str: Optional[str], technique_name_map: Dict[str, str]) -> List[Dict[str, str]]:
    """Build attackTechnique list from comma-separated technique IDs and name map."""
    if not techniques_str:
        return []
    result = []
    for tid in techniques_str.split(","):
        tid = tid.strip()
        if tid:
            result.append({"name": technique_name_map.get(tid, ""), "techniqueid": tid})
    return result


def _build_attack_technique_json(techniques_str: Optional[str], technique_name_map: Dict[str, str]) -> Optional[str]:
    """Same as _build_attack_technique but returns JSON string.

    The FortiSOAR connector checks 'techniqueid' in attackTechnique (string check)
    then calls json.loads() on it, so the field must be a JSON string, not a list.
    """
    items = _build_attack_technique(techniques_str, technique_name_map)
    if not items:
        return None
    return json.dumps(items)


def _str_to_list(v: Any) -> List[str]:
    if isinstance(v, str) and v:
        return [x.strip() for x in v.split(",")]
    if isinstance(v, list):
        return v
    return []


def _enrich_incidents(incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add human-readable fields and parse structured strings."""
    for inc in incidents:
        status = inc.get("incidentStatus")
        if status is not None:
            inc["incidentStatusStr"] = INCIDENT_STATUS.get(int(status), "")
        for field in ("incidentSrc", "incidentTarget"):
            raw = inc.get(field)
            if raw and isinstance(raw, str):
                d: Dict[str, str] = {}
                for pair in raw.split(","):
                    if ":" in pair:
                        idx = pair.index(":")
                        d[pair[:idx].strip()] = pair[idx + 1:].strip()
                inc[field] = d
        attack = inc.get("attackTechnique")
        if attack and "techniqueid" in str(attack):
            try:
                inc["attackTechnique"] = json.loads(attack)
            except Exception:
                pass
    return {"data": incidents}


class IncidentService:
    def __init__(self, repo: IncidentRepository):
        self._repo = repo

    async def list_incidents(self, req: IncidentListRequest) -> Dict[str, Any]:
        filters: Dict[str, Any] = dict(req.search) if req.search else {}

        if req.incidentStatus:
            filters["status"] = [PARAMS_MAPPING[s] for s in req.incidentStatus if s in PARAMS_MAPPING]
        if req.incidentCategory:
            filters["phIncidentCategory"] = [
                INCIDENT_CATEGORY_MAPPING[c] for c in req.incidentCategory if c in INCIDENT_CATEGORY_MAPPING
            ]
        if req.incidentSubCategory:
            filters["phSubIncidentCategory"] = _str_to_list(req.incidentSubCategory)
        if req.severity:
            filters["eventSeverityCat"] = req.severity
        if req.eventType:
            filters["eventType"] = _str_to_list(req.eventType)

        order_field = "incidentLastSeen"
        descending = True
        if req.orderBy:
            parts = req.orderBy.split()
            if len(parts) == 2:
                order_field = parts[0]
                descending = parts[1].upper() == "DESC"

        incidents = await self._repo.list_incidents(
            filters=filters,
            start=req.start,
            size=req.size,
            time_from_ms=to_milliseconds(req.timeFrom) or None,
            time_to_ms=to_milliseconds(req.timeTo) or None,
            order_field=order_field,
            descending=descending,
            fields=req.fields,
        )
        return _enrich_incidents(incidents)

    async def get_detail(self, req: IncidentDetailRequest) -> Any:
        ids = req.incidentId if isinstance(req.incidentId, list) else [req.incidentId]
        return await self._repo.get_by_ids(
            incident_ids=ids,
            time_from_ms=to_milliseconds(req.timeFrom) or None,
            time_to_ms=to_milliseconds(req.timeTo) or None,
        )

    async def update(self, req: UpdateIncidentRequest) -> Dict[str, Any]:
        status = PARAMS_MAPPING.get(req.incidentStatus, req.incidentStatus) if req.incidentStatus else None
        resolution = PARAMS_MAPPING.get(req.resolution, "") if req.resolution else None
        ok = await self._repo.update_incident(req.incidentId, status, resolution)
        return {
            "message": "Incident updated" if ok else "Provided incident does not exist",
            "incident_id": req.incidentId,
        }

    async def comment(self, req: CommentIncidentRequest) -> Dict[str, Any]:
        ok = await self._repo.add_comment(req.id, req.comment_text)
        return {
            "message": "Successfully added comment to incident" if ok else "Provided incident does not exist",
            "incident_id": req.id,
        }

    async def clear(self, req: ClearIncidentRequest) -> Dict[str, Any]:
        ok = await self._repo.clear_incident(req.id, req.comment_text)
        return {
            "message": "Successfully cleared specified incident" if ok else "Provided incident does not exist",
            "incident_id": req.id,
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
    ) -> Dict[str, Any]:
        if filters:
            # DB stores severity_cat as uppercase (e.g. "HIGH", "MEDIUM", "LOW")
            if filters.get("eventSeverityCat"):
                filters["eventSeverityCat"] = [v.upper() for v in filters["eventSeverityCat"]]
            # status may arrive as strings (e.g. ["0"]) — coerce to int
            for key in ("status", "incidentStatus"):
                if filters.get(key):
                    filters[key] = [int(v) for v in filters[key]]

        rows = await self._repo.list_pub_incidents(
            time_from_ms=time_from_ms,
            time_to_ms=time_to_ms,
            size=size,
            start=start,
            filters=filters,
            order_by=order_by,
            descending=descending,
        )
        result = []
        for row in rows:
            rule_info = _parse_rule_xml(row.get("rule_xml"))
            status = row.get("incident_status") or 0

            detail = row.get("incident_detail_json")
            if isinstance(detail, dict):
                detail = json.dumps(detail)

            result.append({
                "count": row.get("incident_count"),
                "customer": row.get("customer"),
                "eventName": rule_info["event_name"],
                "eventType": rule_info["event_type"],
                "incidentId": row.get("inst_incident_id"),
                # connector의 update_attr_data()가 직접 split(',')으로 파싱하므로 raw 문자열 반환
                "incidentSrc": row.get("incident_src") or "",
                "attackTactic": row.get("tactics"),
                "incidentReso": row.get("incident_reso"),
                "eventSeverity": row.get("severity"),
                "incidentRptIp": row.get("orig_device_ip"),
                "incidentTitle": row.get("incident_title"),
                "incidentDetail": detail,
                "incidentStatus": status,
                # connector의 update_attr_data()가 직접 split(',')으로 파싱하므로 raw 문자열 반환
                "incidentTarget": row.get("incident_target") or "",
                # connector가 'techniqueid' in str 체크 후 json.loads() 하므로 JSON 문자열 반환
                "attackTechnique": _build_attack_technique_json(
                    row.get("techniques"), rule_info["technique_names"]
                ),
                "incidentTagName": row.get("tag_name"),
                "eventSeverityCat": row.get("severity_cat"),
                "incidentLastSeen": row.get("last_seen_time"),
                "incidentFirstSeen": row.get("first_seen_time"),
                "incidentStatusStr": PUB_INCIDENT_STATUS_STR.get(int(status), ""),
                "incidentRptDevName": row.get("orig_device_name"),
                "phIncidentCategory": row.get("rule_category"),
                "incidentClearedTime": row.get("cleared_time") or 0,
                "phSubIncidentCategory": row.get("ph_incident_category"),
            })
        return {"data": result, "total": len(result), "pages": 1, "queryId": None}

    async def get_associated_events(
        self,
        incident_id: int,
        per_page: int = 10,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
    ) -> Any:
        # NOTE: EventRepository is ClickHouse-based; injected separately when needed.
        # This method signature is kept for router compatibility.
        # TODO: inject EventRepository via constructor if this service needs it
        raise NotImplementedError("TODO: inject EventRepository and call get_events_by_incident")


# ---------------------------------------------------------------------------
# Triggering events — Redis Queue (start → progress → result)
# ---------------------------------------------------------------------------


def _serialize_value(v: Any) -> Any:
    """Convert ClickHouse types that are not JSON-serializable to plain Python types."""
    import ipaddress
    if isinstance(v, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return [_serialize_value(i) for i in v]
    if isinstance(v, dict):
        return {k: _serialize_value(val) for k, val in v.items()}
    return v


def _build_triggering_event(row: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Map a ClickHouse rawevents row to FortiSIEM triggeringEvents response format."""
    event_id = row.get("eventId")

    # phRecvTime is a Python datetime (UTC) returned by clickhouse-connect; convert to epoch ms
    recv = row.get("phRecvTime")
    if isinstance(recv, datetime):
        receive_time = int(recv.replace(tzinfo=timezone.utc).timestamp() * 1000)
    elif isinstance(recv, (int, float)):
        receive_time = int(recv) * 1000 if recv < 10_000_000_000 else int(recv)
    else:
        receive_time = None

    # Known top-level columns — everything else goes into attributes
    _top_level = {"eventId", "phCustId", "custId", "phRecvTime", "rawEventMsg", "eventType"}
    attributes = {k: _serialize_value(v) for k, v in row.items() if k not in _top_level}

    return {
        "custId": row.get("phCustId") or row.get("custId"),
        "index": index,
        "id": event_id,
        "eventType": row.get("eventType", ""),
        "receiveTime": receive_time,
        "rawMessage": row.get("rawEventMsg", ""),
        "nid": str(event_id) if event_id is not None else "",
        "attributes": attributes,
        "eventAttributes": [],
        "dataStr": {},
    }


class TriggeringEventsService:
    """
    3-step async flow for /phoenix/rest/pub/incident/triggeringEvents/*.

    start_query  → enqueues a job to Redis Queue, returns queryId immediately.
    get_progress → polls rq job status (queued=0 / started=50 / finished=100 / failed=-1).
    get_result   → reads job.result from Redis.

    Heavy DB work (PostgreSQL + ClickHouse) runs in a separate worker process.
    """

    def __init__(self, redis_conn: "Redis"):
        self._redis = redis_conn

    async def start_query(self, incident_id: int, size: int = 100) -> str:
        from rq import Queue as RQueue
        from app.core.config import get_settings
        from app.queue.jobs import process_triggering_events

        s = get_settings()
        query_id = str(random.randint(1_000_000, 9_999_999))
        q = RQueue(s.redis_queue_name, connection=self._redis)
        q.enqueue(
            process_triggering_events,
            incident_id,
            size,
            job_id=query_id,
            result_ttl=s.redis_result_ttl,
            failure_ttl=s.redis_failure_ttl,
        )
        logger.debug("enqueued job %s for incident=%s size=%s", query_id, incident_id, size)
        return query_id

    def get_progress(self, query_id: str) -> Dict[str, Any]:
        from rq.job import Job, JobStatus
        try:
            job = Job.fetch(query_id, connection=self._redis)
            status = job.get_status()
            if status == JobStatus.FINISHED:
                pct = 100
            elif status == JobStatus.FAILED:
                pct = -1
            elif status == JobStatus.STARTED:
                pct = 50
            else:
                pct = 0
        except Exception:
            pct = 0
        return {"progressPct": pct}

    def get_result(self, query_id: str) -> Dict[str, Any]:
        from rq.job import Job
        try:
            job = Job.fetch(query_id, connection=self._redis)
            data = job.result or []
        except Exception:
            data = []
        return {
            "queryId": None,
            "progressPct": None,
            "data": data,
            "result": {
                "code": 0,
                "description": f"{len(data)} data found in this time range",
                "details": None,
            },
        }
