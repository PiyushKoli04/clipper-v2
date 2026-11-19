"""Stage 6: Generate Instagram caption + hashtags via Gemini."""

from __future__ import annotations

import json
import os
import re

from worker.config import ClipperConfig
from worker.utils import FreeTierLimitError, log, retry

CAPTION_PROMPT = """You are a social media expert. Write an Instagram Reel caption for this clip.

CLIP INFO:
- Title: {hook_title}
- Transcript: {transcript}
- Virality score: {score}/100

RULES:
1. First line: attention-grabbing hook (use an emoji).
2. 2-3 short sentences max, conversational tone.
3. End with a call-to-action (follow, like, comment, save).
4. Add 5-8 relevant hashtags on the last line. Include these defaults: {default_hashtags}
5. Total caption under 300 characters (excluding hashtags).

Respond ONLY with valid JSON, no markdown:
{{
  "caption": "<the caption text without hashtags>",
  "hashtags": "<space-separated hashtags>"
}}
"""


def _extract_clip_transcript(
    words: list[dict], start: float, end: float,
) -> str:
    """Extract the transcript text for a specific clip time range."""
    return " ".join(
        w["word"] for w in words if w["end"] > start and w["start"] < end
    )


@retry(max_attempts=2, base_delay=5.0)
def _call_gemini_caption(prompt: str) -> dict:
    """Call Gemini and parse caption JSON response."""
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
                "temperature": 0.7,
            },
        },
        timeout=30.0,
    )

    if response.status_code == 429:
        raise FreeTierLimitError("Gemini rate limit hit")
    response.raise_for_status()

    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    text = re.sub(r"```(?:json)?\s*", "", text).strip().strip("`")
    return json.loads(text)


def generate_caption(
    words: list[dict], highlight: dict, config: ClipperConfig,
) -> dict[str, str]:
    """
    Generate an Instagram caption and hashtags for a clip.

    Returns dict with keys: ig_caption, hashtags.
    """
    transcript = _extract_clip_transcript(
        words, highlight["start"], highlight["end"],
    )

    prompt = CAPTION_PROMPT.format(
        hook_title=highlight["hook_title"],
        transcript=transcript[:500],
        score=highlight["virality_score"],
        default_hashtags=config.hashtags_default,
    )

    result = _call_gemini_caption(prompt)
    caption = result.get("caption", highlight["hook_title"])
    hashtags = result.get("hashtags", config.hashtags_default)

    log.info(
        "Caption for '%s': %s... %s",
        highlight["hook_title"], caption[:50], hashtags[:40],
    )

    return {"ig_caption": caption, "hashtags": hashtags}

