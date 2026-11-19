"""Abstract storage backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


class StorageBackend(ABC):
    """Pluggable storage interface for video clips and thumbnails."""

    @abstractmethod
    def upload(
        self, local_path: Path, remote_key: str, content_type: str = "video/mp4"
    ) -> dict:
        """Upload a file. Returns {storage_file_id, video_url, preview_url}."""
        ...

    @abstractmethod
    def delete(self, remote_key: str) -> None:
        """Delete a file from storage."""
        ...

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[dict]:
        """List files. Returns [{key, size, last_modified}]."""
        ...

    @abstractmethod
    def cleanup_old(self, retention_days: int) -> int:
        """Delete files older than retention_days. Returns count deleted."""
        ...

