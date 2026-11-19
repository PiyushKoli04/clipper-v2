"""Notifications API routes."""

from fastapi import APIRouter, Depends
from server.auth import get_current_user
from worker import firestore

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications_endpoint(
    unread_only: bool = False,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    """List recent notifications."""
    return firestore.list_notifications(unread_only=unread_only, limit=limit)


@router.patch("/{notif_id}/read")
def mark_read_endpoint(notif_id: str, user: dict = Depends(get_current_user)):
    """Mark a notification as read."""
    db = firestore._get_db()
    db.collection("notifications").document(notif_id).update({"read": True})
    return {"id": notif_id, "read": True}

