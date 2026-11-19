"""Firestore read/write helpers.

Wraps firebase-admin for all Firestore operations used by the worker
and the dashboard backend.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from worker.utils import log

_db = None


def _get_db():
    """Lazy-init Firestore client from FIREBASE_SA_JSON env var."""
    global _db
    if _db is not None:
        return _db

    import firebase_admin
    from firebase_admin import credentials, firestore

    sa_json = os.environ.get("FIREBASE_SA_JSON", "")
    if not sa_json:
        raise RuntimeError("FIREBASE_SA_JSON env var not set")

    cred_dict = json.loads(sa_json)
    cred = credentials.Certificate(cred_dict)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    log.info("Firestore client initialized")
    return _db


# ── Config ───────────────────────────────────────────────────────────


def get_config() -> dict[str, Any]:
    """Read config/main document."""
    db = _get_db()
    doc = db.collection("config").document("main").get()
    if doc.exists:
        return doc.to_dict()
    return {}


def set_config(data: dict[str, Any]) -> None:
    """Write config/main document (merge)."""
    db = _get_db()
    db.collection("config").document("main").set(data, merge=True)
    log.info("Config updated")


# ── Jobs ─────────────────────────────────────────────────────────────


def get_job(job_id: str) -> dict[str, Any] | None:
    """Read a job document."""
    db = _get_db()
    doc = db.collection("jobs").document(job_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def create_job(job_id: str, data: dict[str, Any]) -> None:
    """Create a new job document."""
    db = _get_db()
    data["created_at"] = datetime.now(timezone.utc)
    data["updated_at"] = datetime.now(timezone.utc)
    db.collection("jobs").document(job_id).set(data)
    log.info("Job created: %s", job_id)


def update_job_status(
    job_id: str,
    status: str,
    stage: str | None = None,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Update job status (one write per stage)."""
    db = _get_db()
    update: dict[str, Any] = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if stage:
        update["stage"] = stage
    if error is not None:
        update["error"] = error
    if extra:
        update.update(extra)

    db.collection("jobs").document(job_id).update(update)
    log.info("Job %s -> %s (stage: %s)", job_id, status, stage or "-")


def get_oldest_queued_job() -> dict[str, Any] | None:
    """Get the oldest job with status 'queued'."""
    db = _get_db()
    docs = (
        db.collection("jobs")
        .where("status", "==", "queued")
        .order_by("created_at")
        .limit(1)
        .get()
    )
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    """List recent jobs, newest first."""
    db = _get_db()
    docs = (
        db.collection("jobs")
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
        .get()
    )
    result = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)
    return result


# ── Clips ────────────────────────────────────────────────────────────


def create_clip(clip_id: str, data: dict[str, Any]) -> None:
    """Create a clip document."""
    db = _get_db()
    data["created_at"] = datetime.now(timezone.utc)
    db.collection("clips").document(clip_id).set(data)
    log.info("Clip created: %s", clip_id)


def update_clip(clip_id: str, data: dict[str, Any]) -> None:
    """Update a clip document (partial)."""
    db = _get_db()
    db.collection("clips").document(clip_id).update(data)


def get_clip(clip_id: str) -> dict[str, Any] | None:
    """Read a clip document."""
    db = _get_db()
    doc = db.collection("clips").document(clip_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def list_clips(
    job_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List clips with optional filters."""
    db = _get_db()
    query = db.collection("clips")

    if job_id:
        query = query.where("job_id", "==", job_id)
    if status:
        query = query.where("status", "==", status)

    query = query.order_by("virality_score", direction="DESCENDING").limit(limit)
    docs = query.get()

    result = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)
    return result


# ── Posted ledger ────────────────────────────────────────────────────


def is_posted(clip_hash: str) -> bool:
    """Check if a clip hash exists in the posted ledger."""
    db = _get_db()
    doc = db.collection("posted").document(clip_hash).get()
    return doc.exists


def mark_posted(clip_hash: str) -> None:
    """Add a clip hash to the posted ledger."""
    db = _get_db()
    db.collection("posted").document(clip_hash).set(
        {"posted_at": datetime.now(timezone.utc)},
    )


# ── Instagram state ─────────────────────────────────────────────────


def get_instagram_state() -> dict[str, Any]:
    """Read state/instagram document."""
    db = _get_db()
    doc = db.collection("state").document("instagram").get()
    if doc.exists:
        return doc.to_dict()
    return {"health": "ok", "posts_today": 0, "session_json": "{}"}


def update_instagram_state(data: dict[str, Any]) -> None:
    """Update state/instagram document (merge)."""
    db = _get_db()
    db.collection("state").document("instagram").set(data, merge=True)


# ── Notifications ────────────────────────────────────────────────────


def create_notification(
    notif_type: str,
    message: str,
    notif_id: str | None = None,
) -> None:
    """Create a notification document."""
    import uuid

    db = _get_db()
    nid = notif_id or str(uuid.uuid4())
    db.collection("notifications").document(nid).set({
        "type": notif_type,
        "message": message,
        "read": False,
        "created_at": datetime.now(timezone.utc),
    })
    log.info("Notification created: [%s] %s", notif_type, message[:60])


def list_notifications(unread_only: bool = False, limit: int = 50) -> list[dict]:
    """List notifications, newest first."""
    db = _get_db()
    query = db.collection("notifications")
    if unread_only:
        query = query.where("read", "==", False)
    query = query.order_by("created_at", direction="DESCENDING").limit(limit)

    result = []
    for doc in query.get():
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)
    return result

