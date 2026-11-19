"""Storage backend factory."""

from __future__ import annotations

from worker.storage.base import StorageBackend


def get_backend(backend_name: str = "r2") -> StorageBackend:
    """Get the configured storage backend."""
    if backend_name == "r2":
        from worker.storage.r2 import R2Backend

        return R2Backend()
    elif backend_name == "gdrive":
        from worker.storage.gdrive import GDriveBackend

        return GDriveBackend()
    else:
        raise ValueError(f"Unknown storage backend: {backend_name}")

