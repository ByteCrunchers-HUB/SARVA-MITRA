"""Supported model locations for the API-only workflow."""

from fastapi import APIRouter, HTTPException

from services.location_service import list_trained_locations

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("", summary="List locations supported by the ML model")
async def get_supported_locations():
    try:
        locations = await list_trained_locations()
        return {"status": "success", "locations": locations}
    except ConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
