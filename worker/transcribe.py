"""Stage 2: Transcription with word-level timestamps.

Primary : Groq Whisper API (whisper-large-v3-turbo)
Fallback: faster-whisper local model ("base")
"""

from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path
from typing import Any

from worker.utils import FreeTierLimitError, log, retry

# Groq limit: 25 MB per request
GROQ_MAX_SIZE = 25 * 1024 * 1024


# ── Audio chunking ───────────────────────────────────────────────────


def _chunk_audio(audio_path: Path, max_size: int = GROQ_MAX_SIZE) -> list[Path]:
    """Split audio into chunks under max_size using ffmpeg."""
    file_size = audio_path.stat().st_size
    if file_size <= max_size:
        return [audio_path]

    # Get duration via ffmpeg stderr
    probe = subprocess.run(
        ["ffmpeg", "-i", str(audio_path), "-hide_banner"],
        capture_output=True, text=True,
    )
    duration = 0.0
    for line in probe.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            duration = (
                float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            )
            break

    n_chunks = math.ceil(file_size / (max_size * 0.9))
    chunk_dur = duration / n_chunks
    chunks: list[Path] = []

    for i in range(n_chunks):
        chunk_path = audio_path.parent / f"chunk_{i:03d}.mp3"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(audio_path),
                "-ss", str(i * chunk_dur), "-t", str(chunk_dur),
                "-ac", "1", "-ar", "16000", "-b:a", "64k",
                str(chunk_path),
            ],
            capture_output=True, check=True, timeout=120,
        )
        chunks.append(chunk_path)

    log.info("Split audio into %d chunks of ~%.0fs each", n_chunks, chunk_dur)
    return chunks


# ── Groq Whisper API ─────────────────────────────────────────────────


@retry(max_attempts=2, base_delay=10.0, exceptions=(Exception,))
def _transcribe_groq(audio_path: Path, offset: float = 0.0) -> list[dict]:
    """Transcribe a single audio file via Groq Whisper API."""
    import httpx

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise FreeTierLimitError("GROQ_API_KEY not set")

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    response = httpx.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": (audio_path.name, audio_data, "audio/mpeg")},
        data={
            "model": "whisper-large-v3-turbo",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        },
        timeout=120.0,
    )

    if response.status_code == 429:
        raise FreeTierLimitError("Groq rate limit hit")
    response.raise_for_status()

    data = response.json()
    return [
        {
            "word": w["word"],
            "start": round(w["start"] + offset, 3),
            "end": round(w["end"] + offset, 3),
        }
        for w in data.get("words", [])
    ]


# ── Local fallback ───────────────────────────────────────────────────


def _transcribe_local(audio_path: Path, offset: float = 0.0) -> list[dict]:
    """Fallback: transcribe using faster-whisper 'base' model locally."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError(
            "faster-whisper not installed. Install with: pip install faster-whisper"
        )

    log.info("Using local faster-whisper fallback")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), word_timestamps=True)

    words: list[dict] = []
    for segment in segments:
        for w in segment.words:
            words.append(
                {
                    "word": w.word.strip(),
                    "start": round(w.start + offset, 3),
                    "end": round(w.end + offset, 3),
                }
            )
    return words


# ── Public API ───────────────────────────────────────────────────────


def transcribe(audio_path: Path) -> dict[str, Any]:
    """
    Transcribe audio with word-level timestamps.

    Returns dict with keys: words, full_text, word_count, method.
    """
    chunks = _chunk_audio(audio_path)
    all_words: list[dict] = []
    method = "groq"
    chunk_offset = 0.0

    for i, chunk in enumerate(chunks):
        log.info("Transcribing chunk %d/%d: %s", i + 1, len(chunks), chunk.name)
        try:
            words = _transcribe_groq(chunk, offset=chunk_offset)
        except (FreeTierLimitError, Exception) as exc:
            log.warning(
                "Groq failed for chunk %d (%s), falling back to local", i + 1, exc,
            )
            words = _transcribe_local(chunk, offset=chunk_offset)
            method = "local"
        all_words.extend(words)
        if words:
            chunk_offset = words[-1]["end"]

    full_text = " ".join(w["word"] for w in all_words)
    log.info("Transcription complete: %d words via %s", len(all_words), method)

    return {
        "words": all_words,
        "full_text": full_text,
        "word_count": len(all_words),
        "method": method,
    }

