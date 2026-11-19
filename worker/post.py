"""Stage 8: Instagram posting via instagrapi.

Handles session persistence in Firestore, rate-limiting, daily caps,
proxy support, and graceful error recovery.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Any

from worker.config import ClipperConfig
from worker.utils import log


# ── Helpers ──────────────────────────────────────────────────────────


def _clip_hash(clip_data: dict) -> str:
    """Generate a deterministic hash for a clip to prevent reposting."""
    key = f"{clip_data.get('job_id', '')}:{clip_data.get('start', '')}:{clip_data.get('end', '')}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def should_post(
    clip_status: str,
    auto_post: bool,
    clip_hash: str,
    posted_hashes: set[str],
    posts_today: int,
    max_posts_per_day: int,
    health: str,
) -> tuple[bool, str]:
    """
    Determine if a clip should be posted.

    Returns (should_post, reason).
    """
    if health != "ok":
        return False, f"Instagram health is '{health}'"

    if clip_hash in posted_hashes:
        return False, "Clip already posted (ledger)"

    if posts_today >= max_posts_per_day:
        return False, f"Daily post limit reached ({posts_today}/{max_posts_per_day})"

    if clip_status == "posted":
        return False, "Clip already has posted status"

    if clip_status == "rejected":
        return False, "Clip is rejected"

    if not auto_post and clip_status != "approved":
        return False, f"Clip status is '{clip_status}', auto_post is off"

    return True, "OK"


def post_clip(
    clip_path: Path,
    caption: str,
    thumbnail_path: Path | None = None,
    config: ClipperConfig | None = None,
) -> dict[str, Any]:
    """
    Post a clip to Instagram Reels via instagrapi.

    Returns dict with keys: ig_media_pk, posted_at.
    """
    try:
        from instagrapi import Client
        from instagrapi.exceptions import (
            ChallengeRequired,
            LoginRequired,
            PleaseWaitFewMinutes,
        )
    except ImportError:
        raise RuntimeError("instagrapi not installed. pip install instagrapi")

    from worker import firestore

    username = os.environ.get("IG_USERNAME", "")
    password = os.environ.get("IG_PASSWORD", "")
    proxy = os.environ.get("IG_PROXY", "")

    if not username or not password:
        raise RuntimeError("IG_USERNAME and IG_PASSWORD must be set")

    cl = Client()

    if proxy:
        cl.set_proxy(proxy)

    # Load session from Firestore
    ig_state = firestore.get_instagram_state()
    session_json = ig_state.get("session_json", "{}")
    if session_json and session_json != "{}":
        try:
            cl.set_settings(json.loads(session_json))
            cl.login(username, password)
            log.info("Loaded existing Instagram session")
        except Exception as e:
            log.warning("Session load failed (%s), doing fresh login", e)
            cl.login(username, password)
    else:
        cl.login(username, password)

    # Save session back
    firestore.update_instagram_state({
        "session_json": json.dumps(cl.get_settings()),
    })

    try:
        media = cl.clip_upload(
            path=str(clip_path),
            caption=caption,
            thumbnail=str(thumbnail_path) if thumbnail_path else None,
        )

        from datetime import datetime, timezone

        result = {
            "ig_media_pk": str(media.pk),
            "posted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Update session + state
        firestore.update_instagram_state({
            "session_json": json.dumps(cl.get_settings()),
            "last_post_at": datetime.now(timezone.utc),
            "posts_today": ig_state.get("posts_today", 0) + 1,
            "health": "ok",
        })

        log.info("Posted to Instagram! media_pk=%s", result["ig_media_pk"])
        return result

    except ChallengeRequired as e:
        log.error("Instagram challenge required: %s", e)
        firestore.update_instagram_state({"health": "challenge"})
        firestore.create_notification("ig_challenge", f"Instagram challenge required: {e}")
        raise

    except LoginRequired as e:
        log.error("Instagram login required: %s", e)
        firestore.update_instagram_state({"health": "login_required"})
        firestore.create_notification("ig_challenge", f"Instagram login required: {e}")
        raise

    except PleaseWaitFewMinutes as e:
        log.error("Instagram rate limit: %s", e)
        firestore.update_instagram_state({"health": "cooldown"})
        raise

    except Exception as e:
        log.error("Instagram posting failed: %s", e)
        raise


def post_delay(config: ClipperConfig) -> None:
    """Random delay between posts."""
    delay = random.randint(config.post_delay_min, config.post_delay_max)
    log.info("Waiting %ds before next post...", delay)
    time.sleep(delay)

