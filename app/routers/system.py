"""
System endpoints.

GET /phoenix/rest/system/health/summary  — fixed health summary response.
"""

from typing import Any, List

from fastapi import APIRouter, Depends

from app.core.auth import require_auth

router = APIRouter(prefix="/phoenix/rest/system", tags=["system"])

_HEALTH_SUMMARY = [
    {
        "id": 1,
        "name": "Super",
        "healthStatus": "Normal",
        "nodes": [
            {"name": "s2.siem.internal", "nodeType": "Super", "status": "Normal", "reason": []},
            {"name": "s3.siem.internal", "nodeType": "Super", "status": "Normal", "reason": []},
            {"name": "s1.siem.internal", "nodeType": "Super", "status": "Normal", "reason": []},
            {"name": "w4.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "w6.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "k3.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "k2.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "w1.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "k1.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "w2.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "w3.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "w5.siem.internal", "nodeType": "Worker", "status": "Normal", "reason": []},
            {"name": "db1.siem.internal", "nodeType": "DBServer", "status": "Normal", "reason": []},
            {"name": "db3.siem.internal", "nodeType": "DBServer", "status": "Normal", "reason": []},
            {"name": "db2.siem.internal", "nodeType": "DBServer", "status": "Normal", "reason": []},
        ],
    },
    {
        "id": 2000,
        "name": "ncom",
        "healthStatus": "Normal",
        "nodes": [
            {"name": "susoft.collector.siem.internal", "nodeType": "Collector", "status": "Normal", "reason": []},
        ],
    },
    {
        "id": 2033,
        "name": "HKT",
        "healthStatus": "Normal",
        "nodes": [
            {"name": "HKT_collector", "nodeType": "Collector", "status": "Normal", "reason": []},
        ],
    },
    {
        "id": 2040,
        "name": "Koreanap",
        "healthStatus": "Normal",
        "nodes": [
            {"name": "koreana_collector1", "nodeType": "Collector", "status": "Normal", "reason": []},
        ],
    },
    {
        "id": 2041,
        "name": "KwangDong",
        "healthStatus": "Normal",
        "nodes": [
            {"name": "KD_collector1", "nodeType": "Collector", "status": "Normal", "reason": []},
        ],
    },
    {
        "id": 2048,
        "name": "SkechersKorea",
        "healthStatus": "Normal",
        "nodes": [
            {"name": "Skx_Collector1", "nodeType": "Collector", "status": "Normal", "reason": []},
        ],
    },
]


@router.get("/health/summary", summary="System health summary")
async def health_summary(
    _auth: str = Depends(require_auth),
) -> List[Any]:
    return _HEALTH_SUMMARY
