from typing import Any

from app.core.auth import require_auth
from fastapi import APIRouter, Depends

from app.dependencies import get_watchlist_service
from app.services.watchlist import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["watchlists"], dependencies=[Depends(require_auth)])


@router.get("", summary="Get all watch lists")
async def get_all(svc: WatchlistService = Depends(get_watchlist_service)) -> Any:
    return await svc.get_all()


@router.get("/count", summary="Get watch list entry count")
async def entry_count(svc: WatchlistService = Depends(get_watchlist_service)) -> Any:
    return await svc.get_entry_count()


@router.get("/{watch_list_id}", summary="Get watch list by ID")
async def get_by_id(
    watch_list_id: int,
    svc: WatchlistService = Depends(get_watchlist_service),
) -> Any:
    return await svc.get_by_id(watch_list_id)


@router.get("/entry/{entry_id}", summary="Get watch list entry by ID")
async def get_entry(
    entry_id: int,
    svc: WatchlistService = Depends(get_watchlist_service),
) -> Any:
    return await svc.get_by_entry_id(entry_id)


@router.post("", summary="Create watch list group")
async def create_group(
    payload: dict,
    svc: WatchlistService = Depends(get_watchlist_service),
) -> Any:
    return await svc.create_group(payload)


@router.post("/{watch_list_id}/entries", summary="Add entries to watch list")
async def add_entries(
    watch_list_id: int,
    entries: list[dict],
    svc: WatchlistService = Depends(get_watchlist_service),
) -> Any:
    return await svc.add_entries(watch_list_id, entries)


@router.delete("/entries", summary="Delete watch list entries by IDs")
async def delete_entries(
    entry_ids: list[int],
    svc: WatchlistService = Depends(get_watchlist_service),
) -> Any:
    return await svc.delete_entries(entry_ids)


@router.delete("", summary="Delete watch lists by IDs")
async def delete_watchlists(
    watchlist_ids: list[int],
    svc: WatchlistService = Depends(get_watchlist_service),
) -> Any:
    return await svc.delete_watchlists(watchlist_ids)
