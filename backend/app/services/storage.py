"""
Pluggable storage interface for LostLink photo uploads.
Supports:
1. Supabase Storage (REST API)
2. Local filesystem storage (development & automated test fallback)
"""
from abc import ABC, abstractmethod
from pathlib import Path
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class StorageProvider(ABC):
    @abstractmethod
    def upload_file(self, file_bytes: bytes, destination_path: str, content_type: str) -> str:
        """Uploads file bytes and returns the accessible public/serving URL."""
        pass

    @abstractmethod
    def delete_file(self, destination_path: str) -> bool:
        """Deletes file at destination_path from storage."""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: Path = settings.STORAGE_LOCAL_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def upload_file(self, file_bytes: bytes, destination_path: str, content_type: str) -> str:
        dest = self.base_dir / destination_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(file_bytes)
        # Return serving URL via /static/uploads/...
        clean_path = destination_path.replace("\\", "/")
        return f"/static/uploads/{clean_path}"

    def delete_file(self, destination_path: str) -> bool:
        dest = self.base_dir / destination_path
        if dest.exists():
            dest.unlink()
            return True
        return False


class SupabaseStorageProvider(StorageProvider):
    def __init__(
        self,
        supabase_url: str = settings.SUPABASE_URL,
        service_key: str = settings.SUPABASE_SERVICE_ROLE_KEY,
        bucket: str = settings.SUPABASE_STORAGE_BUCKET,
    ):
        self.supabase_url = supabase_url.rstrip("/")
        self.service_key = service_key
        self.bucket = bucket

    def _headers(self, content_type: str = "application/json") -> dict:
        return {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "Content-Type": content_type,
        }

    def upload_file(self, file_bytes: bytes, destination_path: str, content_type: str) -> str:
        if not self.supabase_url or not self.service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured for Supabase Storage.")

        clean_path = destination_path.replace("\\", "/").lstrip("/")
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{clean_path}"
        headers = self._headers(content_type=content_type)
        headers["x-upsert"] = "true"

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, content=file_bytes)
            if resp.status_code not in (200, 201):
                logger.error(f"Supabase upload failed [{resp.status_code}]: {resp.text}")
                raise RuntimeError(f"Storage upload failed with status {resp.status_code}: {resp.text}")

        # Construct public URL
        return f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{clean_path}"

    def delete_file(self, destination_path: str) -> bool:
        if not self.supabase_url or not self.service_key:
            return False

        clean_path = destination_path.replace("\\", "/").lstrip("/")
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{clean_path}"
        headers = self._headers()

        with httpx.Client(timeout=10.0) as client:
            resp = client.delete(url, headers=headers)
            return resp.status_code in (200, 204)


def get_storage_provider() -> StorageProvider:
    """Factory returning configured storage provider with automatic local fallback."""
    if settings.STORAGE_PROVIDER == "supabase" and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        return SupabaseStorageProvider()
    return LocalStorageProvider()

