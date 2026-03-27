from fastapi import APIRouter, Depends

from app.dependencies import get_health_service
from app.schemas.common import HealthResponse
from app.services.health import HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Health check (PostgreSQL + ClickHouse)")
async def health(svc: HealthService = Depends(get_health_service)):
    return await svc.check()
