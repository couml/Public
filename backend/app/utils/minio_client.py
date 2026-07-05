from __future__ import annotations

"""MinIO client wrapper with in-memory fallback."""

import io
import os
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings


class MockMinIO:
    """In-memory MinIO replacement when MinIO server is unavailable."""

    def __init__(self):
        self._objects: dict = {}

    def fput_object(self, bucket: str, object_name: str, file_path: str, content_type: str = "") -> Any:
        with open(file_path, "rb") as f:
            self._objects[object_name] = f.read()
        return type("Result", (), {"object_name": object_name})()

    def put_object(self, bucket: str, object_name: str, data: bytes, length: int, content_type: str = "") -> Any:
        self._objects[object_name] = data[:length]
        return type("Result", (), {"object_name": object_name})()

    def get_object(self, bucket: str, object_name: str) -> Any:
        if object_name not in self._objects:
            raise HTTPException(status_code=404, detail=f"Object not found: {object_name}")
        data = self._objects[object_name]
        return type("Response", (), {
            "data": data,
            "read": lambda: data,
            "close": lambda: None,
            "release_conn": lambda: None,
        })()

    def fget_object(self, bucket: str, object_name: str, file_path: str) -> None:
        if object_name not in self._objects:
            raise HTTPException(status_code=404, detail=f"Object not found: {object_name}")
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(self._objects[object_name])

    def remove_object(self, bucket: str, object_name: str) -> None:
        self._objects.pop(object_name, None)

    def presigned_get_object(self, bucket: str, object_name: str, expires: int = 3600) -> str:
        return f"mock://{bucket}/{object_name}"

    def bucket_exists(self, name: str) -> bool:
        return True

    def make_bucket(self, name: str) -> None:
        pass


class MinioClientWrapper:
    def __init__(self):
        try:
            from minio import Minio
            client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            # Test if MinIO is actually reachable
            client.bucket_exists(settings.MINIO_BUCKET)
            self.client = client
            self._mock = None
            print("MinIO connected.")
        except Exception:
            self.client = None
            self._mock = MockMinIO()
            print("MinIO not available, using mock mode.")

    def ensure_bucket(self, name: str) -> None:
        if self._mock:
            return
        try:
            found = self.client.bucket_exists(name)
            if not found:
                self.client.make_bucket(name)
        except Exception:
            pass

    def upload_file(self, object_name: str, file_path: str, content_type: str) -> str:
        if self._mock:
            return self._mock.fput_object(settings.MINIO_BUCKET, object_name, file_path, content_type).object_name
        try:
            from minio.error import S3Error
            result = self.client.fput_object(settings.MINIO_BUCKET, object_name, file_path, content_type=content_type)
            return result.object_name
        except S3Error as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"MinIO upload failed: {e}")

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        if self._mock:
            return self._mock.presigned_get_object(settings.MINIO_BUCKET, object_name, expires)
        try:
            from minio.error import S3Error
            return self.client.presigned_get_object(settings.MINIO_BUCKET, object_name, expires=expires)
        except S3Error as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"MinIO presigned URL failed: {e}")

    def download_file(self, object_name: str, file_path: str) -> None:
        if self._mock:
            self._mock.fget_object(settings.MINIO_BUCKET, object_name, file_path)
            return
        try:
            from minio.error import S3Error
            self.client.fget_object(settings.MINIO_BUCKET, object_name, file_path)
        except S3Error as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MinIO download failed: {e}")

    def delete_object(self, object_name: str) -> None:
        if self._mock:
            self._mock.remove_object(settings.MINIO_BUCKET, object_name)
            return
        try:
            from minio.error import S3Error
            self.client.remove_object(settings.MINIO_BUCKET, object_name)
        except S3Error as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"MinIO delete failed: {e}")

    def get_object(self, object_name: str) -> Any:
        if self._mock:
            return self._mock.get_object(settings.MINIO_BUCKET, object_name)
        try:
            from minio.error import S3Error
            return self.client.get_object(settings.MINIO_BUCKET, object_name)
        except S3Error as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MinIO get object failed: {e}")


minio_client = MinioClientWrapper()
