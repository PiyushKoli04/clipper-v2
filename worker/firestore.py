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
    """Lazy-init Firestore client from FIREBASE_SA_JSON env var or service-account.json."""
    global _db
    if _db is not None:
        return _db

    import firebase_admin
    from firebase_admin import credentials, firestore

    sa_raw = os.environ.get("FIREBASE_SA_JSON", "").strip()
    # Strip wrapping quotes if any
    if (sa_raw.startswith("'") and sa_raw.endswith("'")) or (sa_raw.startswith('"') and sa_raw.endswith('"')):
        sa_raw = sa_raw[1:-1].strip()

    cred_dict = None

    if sa_raw:
        if sa_raw.startswith("{"):
            try:
                cred_dict = json.loads(sa_raw)
            except Exception as e:
                log.error("Failed to parse FIREBASE_SA_JSON string: %s", e)
        elif os.path.exists(sa_raw):
            with open(sa_raw, "r", encoding="utf-8") as f:
                cred_dict = json.load(f)

    # Check local service-account.json in root
    if not cred_dict:
        root_dir = Path(__file__).resolve().parent.parent
        for fname in ("service-account.json", "serviceAccount.json", "firebase-key.json"):
            cand = root_dir / fname
            if cand.exists():
                log.info("Found local service account file: %s", cand)
                with open(cand, "r", encoding="utf-8") as f:
                    cred_dict = json.load(f)
                break

    if not cred_dict:
        raise RuntimeError("No valid Firebase service account found. Set FIREBASE_SA_JSON or provide service-account.json")

    cred = credentials.Certificate(cred_dict)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    log.info("Firestore client successfully connected to project: %s", cred_dict.get("project_id"))
    return _db


# ── Config ───────────────────────────────────────────────────────────


_local_store: dict[str, dict[str, Any]] = {
    "config": {"main": {}},
    "jobs": {},
    "clips": {},
    "posted": {},
    "state": {"instagram": {"health": "ok", "posts_today": 0, "session_json": "{}"}},
    "notifications": {},
}


def _sanitize_doc(d: dict[str, Any]) -> dict[str, Any]:
    """Ensure all datetime and Timestamp fields are JSON-serializable."""
    res = {}
    for k, v in d.items():
        if hasattr(v, "isoformat"):
            res[k] = v.isoformat()
        elif hasattr(v, "timestamp"):
            try:
                res[k] = datetime.fromtimestamp(v.timestamp(), tz=timezone.utc).isoformat()
            except Exception:
                res[k] = str(v)
        elif isinstance(v, dict):
            res[k] = _sanitize_doc(v)
        elif isinstance(v, list):
            res[k] = [_sanitize_doc(item) if isinstance(item, dict) else item for item in v]
        else:
            res[k] = v
    return res


def get_config() -> dict[str, Any]:
    """Read config/main document."""
    try:
        db = _get_db()
        doc = db.collection("config").document("main").get()
        if doc.exists:
            return _sanitize_doc(doc.to_dict())
    except Exception as e:
        log.warning("Firestore get_config failed (%s), using local fallback", e)
    return _sanitize_doc(_local_store["config"].get("main", {}))


def set_config(data: dict[str, Any]) -> None:
    """Write config/main document (merge)."""
    _local_store["config"]["main"].update(data)
    try:
        db = _get_db()
        db.collection("config").document("main").set(data, merge=True)
        log.info("Config updated in Firestore")
    except Exception as e:
        log.warning("Firestore set_config failed (%s), stored in local fallback", e)


def get_job(job_id: str) -> dict[str, Any] | None:
    """Read a job document."""
    try:
        db = _get_db()
        doc = db.collection("jobs").document(job_id).get()
        if doc.exists:
            data = _sanitize_doc(doc.to_dict())
            data["id"] = doc.id
            return data
    except Exception as e:
        log.warning("Firestore get_job failed (%s), checking local", e)
    res = _local_store["jobs"].get(job_id)
    return _sanitize_doc(res) if res else None


def create_job(job_id: str, data: dict[str, Any]) -> None:
    """Create a new job document."""
    now = datetime.now(timezone.utc)
    data["created_at"] = now
    data["updated_at"] = now
    data["id"] = job_id
    _local_store["jobs"][job_id] = _sanitize_doc(data)

    db = _get_db()
    db.collection("jobs").document(job_id).set(data)
    log.info("Job successfully created in Firestore: %s", job_id)


def update_job_status(
    job_id: str,
    status: str,
    stage: str | None = None,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Update job status (one write per stage)."""
    now = datetime.now(timezone.utc)
    update: dict[str, Any] = {
        "status": status,
        "updated_at": now,
    }
    if stage:
        update["stage"] = stage
    if error is not None:
        update["error"] = error
    if extra:
        update.update(extra)

    if job_id in _local_store["jobs"]:
        _local_store["jobs"][job_id].update(update)

    try:
        db = _get_db()
        db.collection("jobs").document(job_id).update(update)
        log.info("Job %s -> %s (stage: %s)", job_id, status, stage or "-")
    except Exception as e:
        log.warning("Firestore update_job_status failed (%s), updated locally", e)


def get_oldest_queued_job() -> dict[str, Any] | None:
    """Get the oldest job with status 'queued'."""
    try:
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
    except Exception as e:
        log.warning("Firestore get_oldest_queued_job failed (%s)", e)

    queued = [j for j in _local_store["jobs"].values() if j.get("status") == "queued"]
    return queued[0] if queued else None


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    """List recent jobs, newest first."""
    try:
        db = _get_db()
        docs = (
            db.collection("jobs")
            .limit(limit)
            .get()
        )
        result = []
        for doc in docs:
            data = _sanitize_doc(doc.to_dict())
            data["id"] = doc.id
            result.append(data)
        if result:
            return sorted(result, key=lambda x: str(x.get("created_at", "")), reverse=True)
    except Exception as e:
        log.warning("Firestore list_jobs failed (%s), returning local jobs", e)

    local_list = [_sanitize_doc(j) for j in _local_store["jobs"].values()]
    return sorted(local_list, key=lambda x: str(x.get("created_at", "")), reverse=True)[:limit]


def create_clip(clip_id: str, data: dict[str, Any]) -> None:
    """Create a clip document."""
    data["created_at"] = datetime.now(timezone.utc)
    data["id"] = clip_id
    _local_store["clips"][clip_id] = data

    try:
        db = _get_db()
        db.collection("clips").document(clip_id).set(data)
        log.info("Clip created in Firestore: %s", clip_id)
    except Exception as e:
        log.warning("Firestore create_clip failed (%s), saved locally", e)


def update_clip(clip_id: str, data: dict[str, Any]) -> None:
    """Update a clip document (partial)."""
    if clip_id in _local_store["clips"]:
        _local_store["clips"][clip_id].update(data)
    try:
        db = _get_db()
        db.collection("clips").document(clip_id).update(data)
    except Exception as e:
        log.warning("Firestore update_clip failed (%s)", e)


def get_clip(clip_id: str) -> dict[str, Any] | None:
    """Read a clip document."""
    try:
        db = _get_db()
        doc = db.collection("clips").document(clip_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
    except Exception as e:
        log.warning("Firestore get_clip failed (%s)", e)
    return _local_store["clips"].get(clip_id)


def list_clips(
    job_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List clips with optional filters."""
    try:
        db = _get_db()
        query = db.collection("clips")
        if job_id:
            query = query.where("job_id", "==", job_id)
        if status:
            query = query.where("status", "==", status)
        docs = query.limit(limit).get()
        result = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            result.append(data)
        if result:
            return sorted(result, key=lambda x: x.get("virality_score", 0), reverse=True)
    except Exception as e:
        log.warning("Firestore list_clips failed (%s), returning local clips", e)

    clips = list(_local_store["clips"].values())
    if job_id:
        clips = [c for c in clips if c.get("job_id") == job_id]
    if status:
        clips = [c for c in clips if c.get("status") == status]
    return sorted(clips, key=lambda x: x.get("virality_score", 0), reverse=True)[:limit]


def is_posted(clip_hash: str) -> bool:
    """Check if a clip hash exists in the posted ledger."""
    try:
        db = _get_db()
        doc = db.collection("posted").document(clip_hash).get()
        return doc.exists
    except Exception:
        return clip_hash in _local_store["posted"]


def mark_posted(clip_hash: str) -> None:
    """Add a clip hash to the posted ledger."""
    _local_store["posted"][clip_hash] = {"posted_at": datetime.now(timezone.utc)}
    try:
        db = _get_db()
        db.collection("posted").document(clip_hash).set(
            {"posted_at": datetime.now(timezone.utc)},
        )
    except Exception as e:
        log.warning("Firestore mark_posted failed (%s)", e)


def get_instagram_state() -> dict[str, Any]:
    """Read state/instagram document."""
    try:
        db = _get_db()
        doc = db.collection("state").document("instagram").get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        log.warning("Firestore get_instagram_state failed (%s)", e)
    return _local_store["state"].get("instagram", {"health": "ok", "posts_today": 0, "session_json": "{}"})


def update_instagram_state(data: dict[str, Any]) -> None:
    """Update state/instagram document (merge)."""
    _local_store["state"]["instagram"].update(data)
    try:
        db = _get_db()
        db.collection("state").document("instagram").set(data, merge=True)
    except Exception as e:
        log.warning("Firestore update_instagram_state failed (%s)", e)


def create_notification(
    notif_type: str,
    message: str,
    notif_id: str | None = None,
) -> None:
    """Create a notification document."""
    import uuid

    nid = notif_id or str(uuid.uuid4())
    notif = {
        "id": nid,
        "type": notif_type,
        "message": message,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _local_store["notifications"][nid] = notif

    try:
        db = _get_db()
        db.collection("notifications").document(nid).set({
            "type": notif_type,
            "message": message,
            "read": False,
            "created_at": datetime.now(timezone.utc),
        })
        log.info("Notification created in Firestore: [%s] %s", notif_type, message[:60])
    except Exception as e:
        log.warning("Firestore create_notification failed (%s), saved locally", e)


def list_notifications(unread_only: bool = False, limit: int = 50) -> list[dict]:
    """List notifications, newest first."""
    try:
        db = _get_db()
        query = db.collection("notifications")
        if unread_only:
            query = query.where("read", "==", False)
        docs = query.limit(limit).get()
        result = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            result.append(data)
        if result:
            return sorted(result, key=lambda x: str(x.get("created_at", "")), reverse=True)
    except Exception as e:
        log.warning("Firestore list_notifications failed (%s), returning local notifications", e)

    notifs = list(_local_store["notifications"].values())
    if unread_only:
        notifs = [n for n in notifs if not n.get("read")]
    return sorted(notifs, key=lambda x: str(x.get("created_at", "")), reverse=True)[:limit]

