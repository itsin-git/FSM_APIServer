"""Time conversion utilities shared across services."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Optional


def to_milliseconds(iso_str: Optional[str]) -> Any:
    if not iso_str:
        return ""
    try:
        return int(time.mktime(time.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ"))) * 1000
    except Exception:
        return ""


def to_epoch(iso_str: str) -> int:
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def epoch_ms_to_utc_str(epoch_ms: int) -> str:
    """Convert epoch milliseconds to UTC datetime string for ClickHouse DateTime columns.

    Example: 1774148880000 → '2026-03-23 03:08:00'
    """
    dt = datetime.utcfromtimestamp(epoch_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


TIME_UNIT_MAP = {"Minutes": 1, "Hours": 60, "Days": 24 * 60}


def build_time_xml(
    rel_time: Optional[str] = None,
    value: int = 0,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
) -> str:
    """Kept for backward compatibility if XML templates are still needed."""
    if time_from and time_to:
        low = to_epoch(time_from)
        high = to_epoch(time_to)
        if low > high:
            return '<Window unit="Minute" val="1"/>'
        return f"<Low>{low}</Low><High>{high}</High>"
    if time_from:
        return f"<Low>{to_epoch(time_from)}</Low>"
    if time_to:
        return f"<High>{to_epoch(time_to)}</High>"
    minutes = TIME_UNIT_MAP.get(rel_time or "", 1) * value if rel_time and value > 0 else 120
    return f'<Window unit="Minute" val="{minutes}"/>'
