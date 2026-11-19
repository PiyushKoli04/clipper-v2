"""Tests for post limit and ledger logic."""

# These test the posting guard logic that will be fully implemented in Step 5.
# For now we test the helper functions that enforce limits.

from datetime import datetime, timezone


def _should_post(
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

    Returns (should_post: bool, reason: str).
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


class TestPostLimits:

    def test_approved_clip_ok(self):
        ok, reason = _should_post("approved", False, "abc", set(), 0, 5, "ok")
        assert ok is True

    def test_rendered_with_auto_post(self):
        ok, reason = _should_post("rendered", True, "abc", set(), 0, 5, "ok")
        assert ok is True

    def test_rendered_without_auto_post(self):
        ok, reason = _should_post("rendered", False, "abc", set(), 0, 5, "ok")
        assert ok is False
        assert "auto_post" in reason

    def test_already_posted_status(self):
        ok, reason = _should_post("posted", True, "abc", set(), 0, 5, "ok")
        assert ok is False

    def test_rejected_clip(self):
        ok, reason = _should_post("rejected", True, "abc", set(), 0, 5, "ok")
        assert ok is False

    def test_already_in_ledger(self):
        ok, reason = _should_post("approved", False, "abc", {"abc"}, 0, 5, "ok")
        assert ok is False
        assert "ledger" in reason

    def test_daily_limit_reached(self):
        ok, reason = _should_post("approved", False, "abc", set(), 5, 5, "ok")
        assert ok is False
        assert "limit" in reason

    def test_bad_health(self):
        ok, reason = _should_post("approved", False, "abc", set(), 0, 5, "challenge")
        assert ok is False
        assert "challenge" in reason

    def test_cooldown_health(self):
        ok, reason = _should_post("approved", False, "abc", set(), 0, 5, "cooldown")
        assert ok is False

