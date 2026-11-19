"""Stage 5: Extract thumbnail frame + compute dominant accent color."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from worker.utils import log


def _extract_frame(clip_path: Path, output_path: Path, timestamp: float = 1.0) -> None:
    """Extract a single frame at the given timestamp, scaled to 540x960."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", str(clip_path),
        "-frames:v", "1",
        "-vf", "scale=540:960",
        "-q:v", "2",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Thumbnail extraction failed: {result.stderr[:300]}")


def _dominant_color(image_path: Path) -> str:
    """Compute the dominant vibrant color hex from a thumbnail image."""
    try:
        from PIL import Image
        import colorsys
    except ImportError:
        log.warning("Pillow not installed, using default accent color")
        return "#6366F1"

    img = Image.open(image_path).convert("RGB").resize((50, 50))
    pixels = list(img.getdata())

    color_counts: dict[tuple[int, int, int], int] = {}
    for r, g, b in pixels:
        qr, qg, qb = (r // 32) * 32, (g // 32) * 32, (b // 32) * 32
        _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if v < 0.15 or s < 0.1:
            continue
        key = (qr, qg, qb)
        color_counts[key] = color_counts.get(key, 0) + 1

    if not color_counts:
        return "#6366F1"

    dominant = max(color_counts, key=lambda k: color_counts[k] * (1 + sum(k) / 765))
    return "#{:02X}{:02X}{:02X}".format(*dominant)


def generate_thumbnail(
    clip_path: Path,
    output_dir: Path,
    clip_index: int,
    timestamp: float = 1.0,
) -> dict[str, Any]:
    """
    Generate a thumbnail for a clip.

    Returns dict with keys: thumbnail_path, accent_color.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = output_dir / f"thumb_{clip_index:02d}.jpg"

    _extract_frame(clip_path, thumb_path, timestamp)
    accent = _dominant_color(thumb_path)

    file_size = thumb_path.stat().st_size / 1024
    log.info(
        "Thumbnail %d: %s (%.0f KB, accent: %s)",
        clip_index, thumb_path.name, file_size, accent,
    )

    return {"thumbnail_path": thumb_path, "accent_color": accent}

