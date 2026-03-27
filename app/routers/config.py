"""
Config endpoints.

GET /phoenix/rest/config/Domain  — list all domains as XML
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.auth import require_auth
from app.dependencies import get_domain_service
from app.services.domain import DomainService

router = APIRouter(prefix="/phoenix/rest/config", tags=["config"])


@router.get("/Domain", summary="List all domains (XML)")
async def list_domains(
    _auth: str = Depends(require_auth),
    svc: DomainService = Depends(get_domain_service),
) -> Response:
    xml_content = await svc.list_domains_xml()
    return Response(content=xml_content, media_type="application/xml")
