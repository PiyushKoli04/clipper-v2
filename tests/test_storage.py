"""Tests for storage interface (mocked)."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from worker.storage.base import StorageBackend


class MockBackend(StorageBackend):
    """In-memory mock storage backend for testing."""

    def __init__(self):
        self.files: dict[str, dict] = {}

    def upload(self, local_path: Path, remote_key: str, content_type: str = "video/mp4") -> dict:
        self.files[remote_key] = {
            "content_type": content_type,
            "size": local_path.stat().st_size if local_path.exists() else 0,
            "uploaded_at": datetime.now(timezone.utc),
        }
        return {
            "storage_file_id": remote_key,
            "video_url": f"https://mock.storage/{remote_key}",
            "preview_url": f"https://mock.storage/{remote_key}?preview",
        }

    def delete(self, remote_key: str) -> None:
        self.files.pop(remote_key, None)

    def list_files(self, prefix: str = "") -> list[dict]:
        return [
            {
                "key": k,
                "size": v["size"],
                "last_modified": v["uploaded_at"],
            }
            for k, v in self.files.items()
            if k.startswith(prefix)
        ]

    def cleanup_old(self, retention_days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        to_delete = [k for k, v in self.files.items() if v["uploaded_at"] < cutoff]
        for k in to_delete:
            del self.files[k]
        return len(to_delete)


class TestStorageInterface:

    def test_upload_returns_urls(self, tmp_path):
        backend = MockBackend()
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"fake video data")

        result = backend.upload(test_file, "clips/test.mp4")
        assert "storage_file_id" in result
        assert "video_url" in result
        assert "preview_url" in result
        assert result["storage_file_id"] == "clips/test.mp4"

    def test_delete(self, tmp_path):
        backend = MockBackend()
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"data")

        backend.upload(test_file, "clips/test.mp4")
        assert len(backend.list_files()) == 1

        backend.delete("clips/test.mp4")
        assert len(backend.list_files()) == 0

    def test_list_with_prefix(self, tmp_path):
        backend = MockBackend()
        test_file = tmp_path / "f.mp4"
        test_file.write_bytes(b"data")

        backend.upload(test_file, "clips/a.mp4")
        backend.upload(test_file, "clips/b.mp4")
        backend.upload(test_file, "thumbs/a.jpg")

        assert len(backend.list_files("clips/")) == 2
        assert len(backend.list_files("thumbs/")) == 1
        assert len(backend.list_files()) == 3

    def test_cleanup_old(self, tmp_path):
        backend = MockBackend()
        test_file = tmp_path / "f.mp4"
        test_file.write_bytes(b"data")

        # Upload a file and backdate it
        backend.upload(test_file, "old.mp4")
        backend.files["old.mp4"]["uploaded_at"] = datetime.now(timezone.utc) - timedelta(days=60)

        backend.upload(test_file, "new.mp4")

        deleted = backend.cleanup_old(retention_days=30)
        assert deleted == 1
        assert len(backend.list_files()) == 1
        assert backend.list_files()[0]["key"] == "new.mp4"

