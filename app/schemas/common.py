from typing import Any, Dict, Optional
from pydantic import BaseModel


class DBStatus(BaseModel):
    ok: bool
    detail: str


class HealthResponse(BaseModel):
    status: str
    postgres: Optional[DBStatus] = None
    clickhouse: Optional[DBStatus] = None


class ErrorResponse(BaseModel):
    detail: str


class GenericResponse(BaseModel):
    message: str
    data: Any = None
