"""Stage 3: AI highlight selection via Gemini.

Send the transcript and get back JSON segments scored for virality.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from worker.config import ClipperConfig
from worker.utils import FreeTierLimitError, log, retry

HIGHLIGHT_PROMPT = """You are an expert short-form video editor. Analyze this transcript and select the {clip_count} best clips for Instagram Reels / TikTok / YouTube Shorts.

RULES:
1. Each clip must be {min_seconds}-{max_seconds} seconds long.
2. Start each clip at a sentence boundary.
3. The hook (attention-grabbing moment) must be within the first 3 seconds.
4. Each clip must be self-contained and make sense without additional context.
5. No overlapping timestamps between clips.
6. Score each clip 0-100 for virality potential.

TRANSCRIPT (with word-level timestamps):
{transcript}

Respond ONLY with valid JSON — no markdown fences, no commentary:
[
  {{
    "start": <start_seconds_float>,
    "end": <end_seconds_float>,
    "hook_title": "<catchy 5-8 word title>",
    "virality_score": <0-100>,
    "reason": "<1-2 sentence explanation of why this clip is engaging>"
  }}
]
"""


# ── Helpers ──────────────────────────────────────────────────────────


def _build_transcript_text(words: list[dict]) -> str:
    """Format word-level timestamps into a readable transcript."""
    lines: list[str] = []
    current_line: list[str] = []

    for w in words:
        current_line.append(w["word"])
        if len(current_line) >= 15 or w["word"].rstrip().endswith((".", "!", "?")):
            lines.append(f"[{w['start']:.1f}s] {' '.join(current_line)}")
            current_line = []
    if current_line:
        lines.append(f"[{words[-1]['start']:.1f}s] {' '.join(current_line)}")
    return "\n".join(lines)


def _extract_json(text: str) -> list[dict]:
    """Extract a JSON array from an LLM response, tolerating markdown fences."""
    text = re.sub(r"```(?:json)?\s*", "", text).strip().strip("`").strip()

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "clips" in result:
            return result["clips"]
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[.*]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:200]}")


def _validate_highlights(
    highlights: list[dict], config: ClipperConfig, duration: float,
) -> list[dict]:
    """Validate and repair highlight segments."""
    valid: list[dict] = []
    seen_ranges: list[tuple[float, float]] = []

    for h in highlights:
        if not all(k in h for k in ("start", "end", "hook_title", "virality_score")):
            log.warning("Skipping highlight missing required fields: %s", h)
            continue

        start = max(0.0, float(h["start"]))
        end = min(float(h["end"]), duration)
        dur = end - start

        if dur < config.min_clip_seconds:
            log.warning("Clip too short (%.1fs < %ds), skipping", dur, config.min_clip_seconds)
            continue
        if dur > config.max_clip_seconds:
            end = start + config.max_clip_seconds
            dur = config.max_clip_seconds
            log.info("Trimmed clip to max %ds", config.max_clip_seconds)

        overlaps = any(start < e and end > s for s, e in seen_ranges)
        if overlaps:
            log.warning("Clip [%.1f-%.1f] overlaps, skipping", start, end)
            continue

        score = max(0, min(100, int(h["virality_score"])))

        valid.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "hook_title": str(h["hook_title"]).strip(),
            "virality_score": score,
            "reason": str(h.get("reason", "")).strip(),
        })
        seen_ranges.append((start, end))

    valid.sort(key=lambda x: x["virality_score"], reverse=True)
    return valid[: config.clips_per_video]


# ── Gemini call ──────────────────────────────────────────────────────


@retry(max_attempts=2, base_delay=5.0)
def _call_gemini(prompt: str) -> str:
    """Call Gemini API and return text response."""
    import httpx

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise FreeTierLimitError("GEMINI_API_KEY not set")

    response = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.3,
            },
        },
        timeout=60.0,
    )

    if response.status_code == 429:
        raise FreeTierLimitError("Gemini rate limit hit")
    response.raise_for_status()

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ── Public API ───────────────────────────────────────────────────────


def select_highlights(
    words: list[dict],
    config: ClipperConfig,
    video_duration: float,
) -> list[dict]:
    """
    Select highlight clips from transcript using Gemini.

    Returns list of validated highlight dicts:
        {start, end, hook_title, virality_score, reason}
    """
    transcript_text = _build_transcript_text(words)

    prompt = HIGHLIGHT_PROMPT.format(
        clip_count=config.clips_per_video,
        min_seconds=config.min_clip_seconds,
        max_seconds=config.max_clip_seconds,
        transcript=transcript_text,
    )

    log.info(
        "Requesting %d highlights from Gemini (video: %.0fs)",
        config.clips_per_video, video_duration,
    )
    response_text = _call_gemini(prompt)

    raw_highlights = _extract_json(response_text)
    highlights = _validate_highlights(raw_highlights, config, video_duration)

    if not highlights:
        raise ValueError("No valid highlights found after validation")

    log.info("Selected %d highlights:", len(highlights))
    for i, h in enumerate(highlights, 1):
        log.info(
            "  %d. [%.1f-%.1f] %s (score: %d)",
            i, h["start"], h["end"], h["hook_title"], h["virality_score"],
        )

    return highlights

