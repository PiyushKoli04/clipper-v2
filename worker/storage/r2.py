"""Cloudflare R2 storage backend (S3-compatible via boto3)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from worker.storage.base import StorageBackend
from worker.utils import log


class R2Backend(StorageBackend):
    """Cloudflare R2 storage using boto3 S3-compatible API."""

    def __init__(self) -> None:
        import boto3

        account_id = os.environ["R2_ACCOUNT_ID"]
        self.bucket_name = os.environ["R2_BUCKET"]
        self.public_url = os.environ.get("R2_PUBLIC_URL", "").rstrip("/")

        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )

    def upload(
        self, local_path: Path, remote_key: str, content_type: str = "video/mp4",
    ) -> dict:
        log.info("Uploading to R2: %s -> %s", local_path.name, remote_key)
        self.s3.upload_file(
            str(local_path),
            self.bucket_name,
            remote_key,
            ExtraArgs={"ContentType": content_type},
        )
        url = (
            f"{self.public_url}/{remote_key}"
            if self.public_url
            else f"r2://{self.bucket_name}/{remote_key}"
        )
        return {
            "storage_file_id": remote_key,
            "video_url": url,
            "preview_url": url,
        }

    def delete(self, remote_key: str) -> None:
        log.info("Deleting from R2: %s", remote_key)
        self.s3.delete_object(Bucket=self.bucket_name, Key=remote_key)

    def list_files(self, prefix: str = "") -> list[dict]:
        paginator = self.s3.get_paginator("list_objects_v2")
        files: list[dict] = []
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for obj in page.get("Contents", []):
                files.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                })
        return files

    def cleanup_old(self, retention_days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        files = self.list_files()
        deleted = 0
        for f in files:
            if f["last_modified"] < cutoff:
                self.delete(f["key"])
                deleted += 1
        log.info("R2 cleanup: deleted %d files older than %d days", deleted, retention_days)
        return deleted

