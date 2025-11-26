"""Health check endpoint."""

from fastapi import APIRouter, Request
from typing import Dict

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check(request: Request) -> Dict[str, any]:
    """
    Health check endpoint.

    Returns application health status and whether cards have been loaded.
    """
    cards_loaded = hasattr(request.app.state, "cards") and len(request.app.state.cards) > 0

    return {"status": "healthy", "cards_loaded": cards_loaded}
