"""Jobs API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from server.auth import get_current_user
from server.models import JobCreateRequest
from server.github import trigger_workflow
from worker import firestore

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
def list_jobs_endpoint(limit: int = 50, user: dict = Depends(get_current_user)):
    """List recent clipping jobs."""
    return firestore.list_jobs(limit=limit)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_job_endpoint(payload: JobCreateRequest, user: dict = Depends(get_current_user)):
    """Create a new clipping job and optionally trigger the GitHub Action worker."""
    job_id = str(uuid.uuid4())
    job_data = {
        "source_url": payload.source_url,
        "status": "queued",
        "stage": "queued",
        "error": None,
        "overrides": payload.overrides.model_dump(exclude_none=True) if payload.overrides else {},
        "github_run_url": None,
    }
    firestore.create_job(job_id, job_data)

    dispatch_res = None
    if payload.run_now:
        dispatch_res = await trigger_workflow(job_id)

    return {
        "id": job_id,
        "status": "queued",
        "dispatched": dispatch_res,
        "message": "Job created",
    }


@router.post("/{job_id}/run")
async def run_job_endpoint(job_id: str, user: dict = Depends(get_current_user)):
    """Trigger the GitHub Action worker for a specific job."""
    job = firestore.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    dispatch_res = await trigger_workflow(job_id)
    return {"job_id": job_id, "dispatch": dispatch_res}


@router.post("/{job_id}/retry")
async def retry_job_endpoint(job_id: str, user: dict = Depends(get_current_user)):
    """Reset a failed job to queued and trigger the worker."""
    job = firestore.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    firestore.update_job_status(job_id, "queued", stage="queued", error=None)
    dispatch_res = await trigger_workflow(job_id)
    return {"job_id": job_id, "status": "queued", "dispatch": dispatch_res}

