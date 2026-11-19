"""Clipper v2 Worker CLI — main entry point.

Usage (local):
    python -m worker.main --url "https://youtube.com/watch?v=..." --dry-run
    python -m worker.main --url "..." --clips 3 --max-seconds 30 --output ./my_clips

Worker mode (GitHub Actions):
    python -m worker.main --job-id <firestore-job-id>
    python -m worker.main --cron

In dry-run mode (default for local), clips render but are not uploaded or posted.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

from worker.config import ClipperConfig, load_config
from worker.download import download_video
from worker.transcribe import transcribe
from worker.highlights import select_highlights
from worker.render import render_all_clips
from worker.thumbnail import generate_thumbnail
from worker.caption import generate_caption
from worker.utils import FreeTierLimitError, TempDir, log


def run_pipeline(
    url: str,
    config: ClipperConfig,
    output_dir: Path | None = None,
    job_id: str | None = None,
    update_status=None,
) -> dict:
    """
    Run the full clipper pipeline on a video URL.

    Args:
        url: Video URL to process.
        config: Pipeline configuration.
        output_dir: Where to save output (None = temp dir auto-cleaned).
        job_id: Firestore job ID (None in local mode).
        update_status: Callback(status, stage, error=None, extra=None) for Firestore.

    Returns a summary dict with clips info.
    """
    job_id = job_id or str(uuid.uuid4())[:8]
    permanent_output = output_dir or Path(f"./output/{job_id}")
    permanent_output.mkdir(parents=True, exist_ok=True)

    def _status(status: str, stage: str, **kwargs):
        if update_status:
            update_status(status, stage, **kwargs)

    with TempDir() as work_dir:
        # ── Stage 1: Download ────────────────────────────────────
        log.info("=" * 60)
        log.info("STAGE 1: DOWNLOAD")
        log.info("=" * 60)
        _status("downloading", "download")
        dl = download_video(url, work_dir)
        video_path = dl["video_path"]
        audio_path = dl["audio_path"]
        source_title = dl["title"]
        video_duration = dl["duration"]

        # ── Stage 2: Transcribe ──────────────────────────────────
        log.info("=" * 60)
        log.info("STAGE 2: TRANSCRIBE")
        log.info("=" * 60)
        _status("transcribing", "transcribe")
        transcript = transcribe(audio_path)
        words = transcript["words"]
        log.info(
            "Transcript: %d words via %s",
            transcript["word_count"], transcript["method"],
        )

        # ── Stage 3: Select highlights ───────────────────────────
        log.info("=" * 60)
        log.info("STAGE 3: SELECT HIGHLIGHTS")
        log.info("=" * 60)
        _status("selecting", "highlights")
        highlights = select_highlights(words, config, video_duration)

        # ── Stage 4: Render clips ────────────────────────────────
        log.info("=" * 60)
        log.info("STAGE 4: RENDER CLIPS")
        log.info("=" * 60)
        _status("rendering", "render")
        clips_dir = permanent_output / "clips"
        render_results = render_all_clips(
            video_path, words, highlights, clips_dir, config,
        )

        # ── Stage 5: Thumbnails ──────────────────────────────────
        log.info("=" * 60)
        log.info("STAGE 5: THUMBNAILS")
        log.info("=" * 60)
        thumbs_dir = permanent_output / "thumbnails"
        for i, render in enumerate(render_results):
            thumb = generate_thumbnail(render["clip_path"], thumbs_dir, i)
            render.update(thumb)

        # ── Stage 6: Captions ────────────────────────────────────
        log.info("=" * 60)
        log.info("STAGE 6: CAPTIONS")
        log.info("=" * 60)
        for i, (render, highlight) in enumerate(zip(render_results, highlights)):
            caption = generate_caption(words, highlight, config)
            render.update(caption)
            highlight.update(caption)

    # ── Build summary ────────────────────────────────────────────
    log.info("=" * 60)
    log.info("PIPELINE COMPLETE")
    log.info("=" * 60)

    clips_summary = []
    for i, (render, highlight) in enumerate(zip(render_results, highlights)):
        clip_info = {
            "index": i,
            "hook_title": highlight["hook_title"],
            "virality_score": highlight["virality_score"],
            "reason": highlight["reason"],
            "start": highlight["start"],
            "end": highlight["end"],
            "duration": render["duration"],
            "clip_path": str(render["clip_path"]),
            "thumbnail_path": str(render.get("thumbnail_path", "")),
            "accent_color": render.get("accent_color", "#6366F1"),
            "ig_caption": render.get("ig_caption", ""),
            "hashtags": render.get("hashtags", ""),
        }
        clips_summary.append(clip_info)
        log.info(
            "  Clip %d: '%s' [%.1f-%.1f] score=%d color=%s",
            i,
            clip_info["hook_title"],
            clip_info["start"],
            clip_info["end"],
            clip_info["virality_score"],
            clip_info["accent_color"],
        )

    if config.dry_run:
        log.info("DRY RUN: Skipping upload and posting.")
        log.info("Clips saved to: %s", clips_dir)

    return {
        "job_id": job_id,
        "source_url": url,
        "source_title": source_title,
        "video_duration": video_duration,
        "clips": clips_summary,
        "config": config.to_dict(),
    }


# ── Firestore-integrated worker mode ────────────────────────────────


def _run_firestore_job(job_id: str) -> None:
    """Run a specific job from Firestore."""
    from worker import firestore
    from worker.config import ClipperConfig
    from worker.storage import get_backend

    # Load config from Firestore
    fs_config = firestore.get_config()
    config = ClipperConfig.from_dict(fs_config) if fs_config else ClipperConfig()

    # Load job
    job = firestore.get_job(job_id)
    if not job:
        log.error("Job %s not found in Firestore", job_id)
        sys.exit(1)

    url = job.get("source_url", "")
    if not url:
        firestore.update_job_status(job_id, "failed", error="No source_url in job")
        sys.exit(1)

    # Apply job overrides
    config = config.apply_overrides(job.get("overrides"))

    # Set github run url
    github_run_url = os.environ.get("GITHUB_RUN_URL", "")

    def update_status(status, stage, error=None, extra=None):
        kw = extra or {}
        if github_run_url:
            kw["github_run_url"] = github_run_url
        firestore.update_job_status(job_id, status, stage, error, kw)

    try:
        result = run_pipeline(
            url=url, config=config, job_id=job_id, update_status=update_status,
        )

        # Upload clips to storage
        if not config.dry_run:
            update_status("uploading", "upload")
            backend = get_backend(config.storage_backend)

            for clip in result["clips"]:
                clip_id = str(uuid.uuid4())
                clip_path = Path(clip["clip_path"])
                thumb_path = Path(clip["thumbnail_path"]) if clip["thumbnail_path"] else None

                # Upload video
                remote_key = f"clips/{job_id}/{clip_path.name}"
                upload_result = backend.upload(clip_path, remote_key, "video/mp4")

                # Upload thumbnail
                thumb_result = {}
                if thumb_path and thumb_path.exists():
                    thumb_key = f"thumbs/{job_id}/{thumb_path.name}"
                    thumb_result = backend.upload(
                        thumb_path, thumb_key, "image/jpeg",
                    )

                # Create clip document in Firestore
                firestore.create_clip(clip_id, {
                    "job_id": job_id,
                    "start": clip["start"],
                    "end": clip["end"],
                    "duration": clip["duration"],
                    "hook_title": clip["hook_title"],
                    "virality_score": clip["virality_score"],
                    "reason": clip["reason"],
                    "ig_caption": clip["ig_caption"],
                    "hashtags": clip["hashtags"],
                    "accent_color": clip["accent_color"],
                    "storage_file_id": upload_result.get("storage_file_id", ""),
                    "video_url": upload_result.get("video_url", ""),
                    "preview_url": upload_result.get("preview_url", ""),
                    "thumbnail_url": thumb_result.get("video_url", ""),
                    "status": "rendered",
                })
        else:
            # Dry run: still save clips to Firestore with local paths
            for clip in result["clips"]:
                clip_id = str(uuid.uuid4())
                firestore.create_clip(clip_id, {
                    "job_id": job_id,
                    "start": clip["start"],
                    "end": clip["end"],
                    "duration": clip["duration"],
                    "hook_title": clip["hook_title"],
                    "virality_score": clip["virality_score"],
                    "reason": clip["reason"],
                    "ig_caption": clip["ig_caption"],
                    "hashtags": clip["hashtags"],
                    "accent_color": clip["accent_color"],
                    "storage_file_id": "",
                    "video_url": "",
                    "preview_url": "",
                    "thumbnail_url": "",
                    "status": "rendered",
                })

        # Mark job done
        update_status("done", "complete")
        firestore.create_notification("job_done", f"Job {job_id} completed with {len(result['clips'])} clips")
        log.info("Job %s completed successfully", job_id)

    except FreeTierLimitError as e:
        update_status("failed", "error", error=f"Free tier limit: {e}")
        firestore.create_notification("job_failed", f"Job {job_id} failed: {e}")
        log.error("FREE TIER LIMIT: %s", e)
        sys.exit(2)

    except Exception as e:
        update_status("failed", "error", error=str(e)[:500])
        firestore.create_notification("job_failed", f"Job {job_id} failed: {e}")
        log.error("Pipeline failed: %s", e, exc_info=True)
        sys.exit(1)


def _run_cron() -> None:
    """Cron mode: check config and pick oldest queued job."""
    from worker import firestore
    from worker.config import ClipperConfig

    # Check if cron is enabled
    fs_config = firestore.get_config()
    config = ClipperConfig.from_dict(fs_config) if fs_config else ClipperConfig()

    if not config.cron_enabled:
        log.info("Cron is disabled in config. Exiting.")
        return

    # Find oldest queued job
    job = firestore.get_oldest_queued_job()
    if not job:
        log.info("No queued jobs found. Exiting.")
        return

    log.info("Cron picked job: %s (%s)", job["id"], job.get("source_url", "?"))
    _run_firestore_job(job["id"])


# ── CLI ──────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clipper v2 — AI-powered short-form video clipper",
    )
    parser.add_argument("--url", type=str, help="Video URL to process (local mode)")
    parser.add_argument("--job-id", type=str, help="Firestore job ID (worker mode)")
    parser.add_argument("--cron", action="store_true", help="Cron mode: pick oldest queued job")
    parser.add_argument("--output", type=str, help="Output directory (local mode)")
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="Skip upload/posting (default: true)",
    )
    parser.add_argument("--no-dry-run", action="store_true", help="Disable dry-run")
    parser.add_argument("--clips", type=int, help="Number of clips to generate")
    parser.add_argument("--min-seconds", type=int, help="Minimum clip length")
    parser.add_argument("--max-seconds", type=int, help="Maximum clip length")

    args = parser.parse_args()

    # ── Cron mode ────────────────────────────────────────────────
    if args.cron:
        _run_cron()
        return

    # ── Firestore job mode ───────────────────────────────────────
    if args.job_id:
        _run_firestore_job(args.job_id)
        return

    # ── Local mode ───────────────────────────────────────────────
    if not args.url:
        parser.error("One of --url, --job-id, or --cron is required")

    config = load_config()
    if args.no_dry_run:
        config.dry_run = False

    overrides: dict = {}
    if args.clips:
        overrides["clip_count"] = args.clips
    if args.min_seconds:
        overrides["min_seconds"] = args.min_seconds
    if args.max_seconds:
        overrides["max_seconds"] = args.max_seconds
    config = config.apply_overrides(overrides)

    output_dir = Path(args.output) if args.output else None

    try:
        result = run_pipeline(url=args.url, config=config, output_dir=output_dir)
        log.info(
            "Done! %d clips generated for '%s'",
            len(result["clips"]), result["source_title"],
        )
    except FreeTierLimitError as e:
        log.error("FREE TIER LIMIT: %s", e)
        sys.exit(2)
    except Exception as e:
        log.error("Pipeline failed: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
