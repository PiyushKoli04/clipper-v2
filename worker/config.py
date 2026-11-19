"""Configuration management: local defaults, overridden by Firestore later."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ClipperConfig:
    """Pipeline configuration with sensible free-tier defaults."""

    storage_backend: str = "r2"
    clips_per_video: int = 4
    min_clip_seconds: int = 20
    max_clip_seconds: int = 45
    caption_style: str = "bold_highlight"
    hashtags_default: str = "#reels #viral #clips"
    dry_run: bool = True
    auto_post: bool = False
    max_posts_per_day: int = 5
    post_delay_min: int = 30
    post_delay_max: int = 180
    face_crop: bool = False
    cron_enabled: bool = False
    retention_days: int = 30

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClipperConfig:
        """Create config from a dict, ignoring unknown keys."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in valid_keys})

    def apply_overrides(self, overrides: dict[str, Any] | None) -> ClipperConfig:
        """Return a new config with job-level overrides applied."""
        if not overrides:
            return self
        data = self.to_dict()
        mapping = {
            "clip_count": "clips_per_video",
            "min_seconds": "min_clip_seconds",
            "max_seconds": "max_clip_seconds",
        }
        for key, val in overrides.items():
            mapped = mapping.get(key, key)
            if mapped in data:
                data[mapped] = val
        return ClipperConfig.from_dict(data)


def load_config() -> ClipperConfig:
    """Load config from defaults (Firestore integration added in Step 2)."""
    return ClipperConfig()

