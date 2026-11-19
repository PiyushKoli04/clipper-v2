"""Stage 1: Download video + extract audio via yt-dlp."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from worker.utils import log, retry


@retry(max_attempts=2, base_delay=5.0)
def download_video(url: str, work_dir: Path, max_height: int = 1080) -> dict:
    """
    Download a video capped at max_height and extract 16 kHz mono audio.

    Returns
    -------
    dict with keys: video_path, audio_path, title, duration
    """
    video_dir = work_dir / "source"
    video_dir.mkdir(exist_ok=True)

    log.info("Downloading video: %s", url)

    # ── Download best video+audio up to 1080p ────────────────────────
    video_template = str(video_dir / "%(title).80s.%(ext)s")
    cmd_video = [
        "yt-dlp",
        "--no-playlist",
        "-f",
        f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]",
        "--merge-output-format", "mp4",
        "-o", video_template,
        "--print-json",
        "--no-warnings",
        url,
    ]

    result = subprocess.run(
        cmd_video, capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()}")

    info = json.loads(result.stdout.strip().split("\n")[-1])
    video_path = Path(info.get("filename") or info.get("_filename", ""))
    title = info.get("title", "Untitled")
    duration = float(info.get("duration", 0))

    if not video_path.exists():
        files = list(video_dir.glob("*.mp4"))
        if not files:
            raise FileNotFoundError("Downloaded video not found")
        video_path = files[0]

    log.info("Video saved: %s (%.0fs)", video_path.name, duration)

    # ── Extract 16 kHz mono mp3 audio ────────────────────────────────
    audio_path = work_dir / "audio.mp3"
    cmd_audio = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000",
        "-b:a", "64k",
        str(audio_path),
    ]
    subprocess.run(cmd_audio, capture_output=True, timeout=300, check=True)
    log.info(
        "Audio extracted: %s (%.1f MB)",
        audio_path.name,
        audio_path.stat().st_size / 1e6,
    )

    return {
        "video_path": video_path,
        "audio_path": audio_path,
        "title": title,
        "duration": duration,
    }

