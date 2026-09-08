import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user_optional
from app.services.watchlist_service import get_watchlist_service

logger = logging.getLogger("trinetra.watchlist_api")

router = APIRouter(prefix="/api/v1/watchlist", tags=["Security Watchlist & Interpol"])


@router.get("/check")
async def check_subject_watchlist(
    name: Optional[str] = Query(None, description="Full name of the individual to verify"),
    document_number: Optional[str] = Query(None, description="Passport or ID document number"),
    birth_date: Optional[str] = Query(None, description="Date of birth in YYYY-MM-DD or YYYY format"),
    country: Optional[str] = Query(None, description="Nationality or issuing country ISO code"),
) -> dict[str, Any]:
    """
    Cross-reference an identity against active INTERPOL Red Notices and SSB Watchlists.
    """
    watchlist_svc = get_watchlist_service()
    clean_name = str(name) if isinstance(name, str) else None
    clean_doc = str(document_number) if isinstance(document_number, str) else None
    clean_dob = str(birth_date) if isinstance(birth_date, str) else None
    clean_country = str(country) if isinstance(country, str) else None

    result = watchlist_svc.check_subject(
        name=clean_name,
        document_number=clean_doc,
        birth_date=clean_dob,
        country=clean_country,
    )
    return {
        "status": "success",
        "data": result,
    }


@router.get("/search")
async def search_watchlist(
    q: str = Query(..., min_length=2, description="Search term (name, offence, or country)"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
) -> dict[str, Any]:
    """
    Search the active Interpol Red Notice database by keyword.
    """
    watchlist_svc = get_watchlist_service()
    query_str = str(q) if isinstance(q, str) else ""
    limit_val = int(limit) if isinstance(limit, (int, str)) and str(limit).isdigit() else 20
    matches = watchlist_svc.search_notices(query=query_str, limit=limit_val)
    return {
        "status": "success",
        "query": q,
        "count": len(matches),
        "results": matches,
    }


@router.get("/stats")
async def get_watchlist_stats() -> dict[str, Any]:
    """
    Get current metadata, synchronization status, and metrics of the Interpol & SSB database.
    """
    watchlist_svc = get_watchlist_service()
    return {
        "status": "success",
        "stats": watchlist_svc.get_stats(),
    }


@router.post("/sync")
async def sync_watchlist_database(
    current_user: Optional[dict[str, Any]] = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    Trigger manual re-synchronization of the Interpol Red Notice dataset from upstream feeds.
    """
    watchlist_svc = get_watchlist_service()
    sync_result = watchlist_svc.sync_dataset()
    return {
        "status": "success" if sync_result.get("success") else "error",
        "result": sync_result,
        "triggered_by": current_user.get("username", "system_operator") if current_user else "anonymous_operator",
    }
