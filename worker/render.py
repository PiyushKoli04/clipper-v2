"""Stage 4: Render clips with ffmpeg.

Center-crop to 9:16 (1080x1920), burn ASS captions with word highlighting,
loudnorm audio, H.264/AAC, target under 100 MB.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

from worker.config import ClipperConfig
from worker.utils import log


# ── ASS subtitle generation ─────────────────────────────────────────

ASS_HEADER = r"""[Script Info]
Title: Clipper Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Style: Default,Inter,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,4,2,2,30,30,120,1
Style: Highlight,Inter,72,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,30,30,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS time format: H:MM:SS.CC"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _generate_ass_captions(
    words: list[dict], clip_start: float, clip_end: float,
) -> str:
    """Generate ASS subtitles with word-by-word karaoke highlight effect."""
    clip_words = [w for w in words if w["end"] > clip_start and w["start"] < clip_end]
    if not clip_words:
        return ASS_HEADER

    lines_text = ASS_HEADER

    # Group words into display lines (3-5 words)
    word_groups: list[list[dict]] = []
    current_group: list[dict] = []

    for w in clip_words:
        current_group.append(w)
        if len(current_group) >= 4 or w["word"].rstrip().endswith((".", "!", "?", ",")):
            word_groups.append(current_group)
            current_group = []
    if current_group:
        word_groups.append(current_group)

    for group in word_groups:
        group_start = group[0]["start"] - clip_start
        group_end = group[-1]["end"] - clip_start

        # Build karaoke-style word highlighting
        ass_text_parts = []
        for w in group:
            w_dur_cs = int((w["end"] - w["start"]) * 100)  # centiseconds
            ass_text_parts.append(r"{\kf" + str(w_dur_cs) + "}" + w["word"])

        ass_text = " ".join(ass_text_parts)
        start_ts = _seconds_to_ass_time(max(0, group_start))
        end_ts = _seconds_to_ass_time(group_end)

        lines_text += f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{ass_text}\n"

    return lines_text


# ── Video probing ────────────────────────────────────────────────────


def _probe_video(video_path: Path) -> dict[str, Any]:
    """Get video dimensions via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data.get("streams", []) if s["codec_type"] == "video"), None,
    )
    if not video_stream:
        raise ValueError("No video stream found")

    return {
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "duration": float(data.get("format", {}).get("duration", 0)),
    }


# ── Crop calculation ─────────────────────────────────────────────────


def _calc_center_crop(
    src_w: int, src_h: int, target_w: int = 1080, target_h: int = 1920,
) -> str:
    """Calculate center crop filter for 9:16 output."""
    target_ratio = target_w / target_h  # 0.5625

    if src_w / src_h > target_ratio:
        # Source is wider -> crop sides
        crop_h = src_h
        crop_w = int(src_h * target_ratio)
    else:
        # Source is taller -> crop top/bottom
        crop_w = src_w
        crop_h = int(src_w / target_ratio)

    x = (src_w - crop_w) // 2
    y = (src_h - crop_h) // 2
    return f"crop={crop_w}:{crop_h}:{x}:{y},scale={target_w}:{target_h}"


# ── Build ffmpeg command (public for testing) ────────────────────────


def build_ffmpeg_command(
    video_path: Path,
    output_path: Path,
    start: float,
    end: float,
    ass_path: Path | None,
    src_width: int,
    src_height: int,
) -> list[str]:
    """Build the ffmpeg command for rendering a clip."""
    duration = end - start
    crop_filter = _calc_center_crop(src_width, src_height)

    vf_parts = [crop_filter]
    if ass_path and ass_path.exists():
        ass_escaped = str(ass_path).replace("\\", "/").replace(":", r"\:")
        vf_parts.append(f"subtitles='{ass_escaped}'")

    vf = ",".join(vf_parts)

    return [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", str(video_path),
        "-t", str(duration),
        "-vf", vf,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-fs", "100M",
        str(output_path),
    ]


# ── Main render function ─────────────────────────────────────────────


def render_clip(
    video_path: Path,
    words: list[dict],
    highlight: dict,
    output_dir: Path,
    clip_index: int,
    config: ClipperConfig,
) -> dict[str, Any]:
    """
    Render a single clip from the source video.

    Returns dict with keys: clip_path, ass_path, duration, index.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    start = highlight["start"]
    end = highlight["end"]
    duration = end - start

    probe = _probe_video(video_path)

    # Generate ASS captions
    ass_content = _generate_ass_captions(words, start, end)
    ass_path = output_dir / f"clip_{clip_index:02d}.ass"
    ass_path.write_text(ass_content, encoding="utf-8")

    # Render
    clip_path = output_dir / f"clip_{clip_index:02d}.mp4"
    cmd = build_ffmpeg_command(
        video_path=video_path,
        output_path=clip_path,
        start=start,
        end=end,
        ass_path=ass_path,
        src_width=probe["width"],
        src_height=probe["height"],
    )

    log.info(
        "Rendering clip %d [%.1f-%.1f] (%.0fs): %s",
        clip_index, start, end, duration, highlight["hook_title"],
    )
    log.info("Command: %s", " ".join(shlex.quote(str(c)) for c in cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        log.error("ffmpeg stderr: %s", result.stderr[-1000:] if result.stderr else "none")
        raise RuntimeError(
            f"ffmpeg render failed for clip {clip_index}: {result.stderr[-500:]}"
        )

    file_size = clip_path.stat().st_size / 1e6
    log.info("Clip %d rendered: %s (%.1f MB)", clip_index, clip_path.name, file_size)

    return {
        "clip_path": clip_path,
        "ass_path": ass_path,
        "duration": duration,
        "index": clip_index,
    }


def render_all_clips(
    video_path: Path,
    words: list[dict],
    highlights: list[dict],
    output_dir: Path,
    config: ClipperConfig,
) -> list[dict]:
    """Render all highlight clips. Returns list of render results."""
    results = []
    for i, h in enumerate(highlights):
        results.append(render_clip(video_path, words, h, output_dir, i, config))
    return results

