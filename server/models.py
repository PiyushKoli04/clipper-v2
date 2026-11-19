"""Pydantic models for API request/response validation."""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl


class ConfigModel(BaseModel):
    storage_backend: Literal["r2", "gdrive"] = "r2"
    clips_per_video: int = Field(default=4, ge=1, le=10)
    min_clip_seconds: int = Field(default=20, ge=10, le=120)
    max_clip_seconds: int = Field(default=45, ge=15, le=180)
    caption_style: str = "bold_highlight"
    hashtags_default: str = "#reels #viral #clips"
    dry_run: bool = True
    auto_post: bool = False
    max_posts_per_day: int = Field(default=5, ge=1, le=50)
    post_delay_min: int = Field(default=30, ge=5, le=3600)
    post_delay_max: int = Field(default=180, ge=10, le=7200)
    face_crop: bool = False
    cron_enabled: bool = False
    retention_days: int = Field(default=30, ge=1, le=365)


class JobOverrides(BaseModel):
    clip_count: Optional[int] = Field(default=None, ge=1, le=10)
    min_seconds: Optional[int] = Field(default=None, ge=10, le=120)
    max_seconds: Optional[int] = Field(default=None, ge=15, le=180)


class JobCreateRequest(BaseModel):
    source_url: str
    overrides: Optional[JobOverrides] = None
    run_now: bool = False


class ClipUpdateRequest(BaseModel):
    ig_caption: Optional[str] = None
    hashtags: Optional[str] = None
    status: Optional[Literal["rendered", "approved", "posted", "rejected"]] = None


class NotificationItem(BaseModel):
    id: str
    type: Literal["job_done", "job_failed", "ig_challenge"]
    message: str
    read: bool = False
    created_at: Any = None

