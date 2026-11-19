"""Clips API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from server.auth import get_current_user
from server.models import ClipUpdateRequest
from server.github import trigger_workflow
from worker import firestore

router = APIRouter(prefix="/api/clips", tags=["clips"])


@router.get("")
def list_clips_endpoint(
    status: Optional[str] = None,
    job_id: Optional[str] = None,
    min_score: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user),
):
    """List clips with optional status, job_id, min_score, and search filters."""
    clips = firestore.list_clips(job_id=job_id, status=status, limit=limit)

    if min_score is not None:
        clips = [c for c in clips if c.get("virality_score", 0) >= min_score]

    if search:
        s = search.lower()
        clips = [
            c for c in clips
            if s in str(c.get("hook_title", "")).lower()
            or s in str(c.get("reason", "")).lower()
            or s in str(c.get("ig_caption", "")).lower()
            or s in str(c.get("hashtags", "")).lower()
        ]

    return clips


@router.get("/{clip_id}")
def get_clip_endpoint(clip_id: str, user: dict = Depends(get_current_user)):
    """Get single clip details."""
    clip = firestore.get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.patch("/{clip_id}")
def update_clip_endpoint(
    clip_id: str,
    payload: ClipUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """Update clip metadata (caption, hashtags, status)."""
    clip = firestore.get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        firestore.update_clip(clip_id, update_data)

    return {"id": clip_id, "updated": update_data}


@router.post("/{clip_id}/post")
async def post_clip_endpoint(
    clip_id: str,
    user: dict = Depends(get_current_user),
):
    """Approve clip and trigger post pipeline."""
    clip = firestore.get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Set approved status
    firestore.update_clip(clip_id, {"status": "approved"})

    # Trigger job's worker workflow if associated with job
    dispatch_res = None
    if clip.get("job_id"):
        dispatch_res = await trigger_workflow(clip["job_id"])

    return {
        "id": clip_id,
        "status": "approved",
        "dispatch": dispatch_res,
        "message": "Clip approved and queued for posting",
    }

