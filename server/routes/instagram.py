"""Instagram health and session status routes."""

from fastapi import APIRouter, Depends
from server.auth import get_current_user
from worker import firestore

router = APIRouter(prefix="/api/instagram", tags=["instagram"])


@router.get("/health")
def get_instagram_health_endpoint(user: dict = Depends(get_current_user)):
    """Get current Instagram connection health and daily posting count."""
    state = firestore.get_instagram_state()
    # Never return raw session json password or private credentials to frontend
    return {
        "health": state.get("health", "ok"),
        "posts_today": state.get("posts_today", 0),
        "last_post_at": state.get("last_post_at"),
        "has_session": bool(state.get("session_json") and state.get("session_json") != "{}"),
    }

