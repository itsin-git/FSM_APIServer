from typing import Any

from app.core.auth import require_auth
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_lookup_table_service
from app.services.lookup_table import LookupTableService

router = APIRouter(prefix="/lookup-tables", tags=["lookup-tables"], dependencies=[Depends(require_auth)])


@router.get("", summary="List all lookup tables")
async def list_tables(svc: LookupTableService = Depends(get_lookup_table_service)) -> Any:
    return await svc.list_tables()


@router.post("", summary="Create lookup table")
async def create_table(
    payload: dict,
    svc: LookupTableService = Depends(get_lookup_table_service),
) -> Any:
    return await svc.create_table(payload)


@router.delete("/{lookup_table_id}", summary="Delete lookup table")
async def delete_table(
    lookup_table_id: str,
    svc: LookupTableService = Depends(get_lookup_table_service),
) -> Any:
    return await svc.delete_table(lookup_table_id)


@router.get("/{lookup_table_id}/data", summary="Get lookup table data")
async def get_table_data(
    lookup_table_id: str,
    svc: LookupTableService = Depends(get_lookup_table_service),
) -> Any:
    return await svc.get_table_data(lookup_table_id)


@router.put("/{lookup_table_id}/data", summary="Update lookup table data")
async def update_table_data(
    lookup_table_id: str,
    key: str = Query(...),
    column_data: Any = None,
    svc: LookupTableService = Depends(get_lookup_table_service),
) -> Any:
    return await svc.update_table_data(lookup_table_id, key, column_data)


@router.delete("/{lookup_table_id}/data", summary="Delete lookup table data by keys")
async def delete_table_data(
    lookup_table_id: str,
    keys_data: list,
    svc: LookupTableService = Depends(get_lookup_table_service),
) -> Any:
    return await svc.delete_table_data(lookup_table_id, keys_data)


@router.get("/{lookup_table_id}/task/{task_id}", summary="Check import task status")
async def check_import_status(
    lookup_table_id: str,
    task_id: str,
    svc: LookupTableService = Depends(get_lookup_table_service),
) -> Any:
    return await svc.check_import_status(lookup_table_id, task_id)
