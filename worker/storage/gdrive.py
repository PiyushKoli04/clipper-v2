"""Google Drive storage backend (OAuth refresh token, personal account)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from worker.storage.base import StorageBackend
from worker.utils import log, retry


class GDriveBackend(StorageBackend):
    """Google Drive storage using OAuth2 refresh token (personal account)."""

    def __init__(self) -> None:
        self.folder_id = os.environ["GDRIVE_FOLDER_ID"]
        self._access_token: str | None = None

    def _get_token(self) -> str:
        if self._access_token:
            return self._access_token

        import httpx

        response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": os.environ["GDRIVE_CLIENT_ID"],
                "client_secret": os.environ["GDRIVE_CLIENT_SECRET"],
                "refresh_token": os.environ["GDRIVE_REFRESH_TOKEN"],
                "grant_type": "refresh_token",
            },
        )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        return self._access_token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    @retry(max_attempts=2, base_delay=5.0)
    def upload(
        self, local_path: Path, remote_key: str, content_type: str = "video/mp4",
    ) -> dict:
        import httpx

        log.info("Uploading to Google Drive: %s", local_path.name)

        metadata = {"name": remote_key, "parents": [self.folder_id]}
        file_size = local_path.stat().st_size

        if file_size < 5 * 1024 * 1024:
            # Simple multipart upload
            response = httpx.post(
                "https://www.googleapis.com/upload/drive/v3/files"
                "?uploadType=multipart&fields=id,webViewLink,webContentLink",
                headers=self._headers(),
                files={
                    "metadata": (
                        "metadata", json.dumps(metadata), "application/json",
                    ),
                    "file": (remote_key, open(local_path, "rb"), content_type),
                },
                timeout=120.0,
            )
        else:
            # Resumable upload
            init_resp = httpx.post(
                "https://www.googleapis.com/upload/drive/v3/files"
                "?uploadType=resumable&fields=id,webViewLink,webContentLink",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=metadata,
                timeout=30.0,
            )
            init_resp.raise_for_status()
            upload_url = init_resp.headers["Location"]

            with open(local_path, "rb") as f:
                response = httpx.put(
                    upload_url,
                    content=f.read(),
                    headers={"Content-Type": content_type},
                    timeout=300.0,
                )

        response.raise_for_status()
        data = response.json()
        file_id = data["id"]

        # Make file readable via link
        try:
            httpx.post(
                f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"role": "reader", "type": "anyone"},
                timeout=10.0,
            )
        except Exception as e:
            log.warning("Could not set Drive permissions: %s", e)

        preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
        video_url = data.get("webContentLink", preview_url)

        return {
            "storage_file_id": file_id,
            "video_url": video_url,
            "preview_url": preview_url,
        }

    def delete(self, remote_key: str) -> None:
        import httpx

        log.info("Deleting from Drive: %s", remote_key)
        httpx.delete(
            f"https://www.googleapis.com/drive/v3/files/{remote_key}",
            headers=self._headers(),
            timeout=10.0,
        ).raise_for_status()

    def list_files(self, prefix: str = "") -> list[dict]:
        import httpx

        files: list[dict] = []
        page_token = None

        while True:
            params: dict[str, Any] = {
                "q": f"'{self.folder_id}' in parents and trashed = false",
                "fields": "nextPageToken, files(id, name, size, modifiedTime)",
                "pageSize": 100,
            }
            if page_token:
                params["pageToken"] = page_token

            response = httpx.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=self._headers(),
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            for f in data.get("files", []):
                files.append({
                    "key": f["id"],
                    "size": int(f.get("size", 0)),
                    "last_modified": datetime.fromisoformat(
                        f["modifiedTime"].replace("Z", "+00:00"),
                    ),
                })

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return files

    def cleanup_old(self, retention_days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        files = self.list_files()
        deleted = 0
        for f in files:
            if f["last_modified"] < cutoff:
                self.delete(f["key"])
                deleted += 1
        log.info(
            "Drive cleanup: deleted %d files older than %d days",
            deleted, retention_days,
        )
        return deleted

