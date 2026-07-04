import os
from typing import Any

from fastapi import HTTPException, status
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class MinioClientWrapper:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

    def ensure_bucket(self, name: str) -> None:
        found = self.client.bucket_exists(name)
        if not found:
            self.client.make_bucket(name)

    def upload_file(self, object_name: str, file_path: str, content_type: str) -> str:
        try:
            result = self.client.fput_object(
                settings.MINIO_BUCKET,
                object_name,
                file_path,
                content_type=content_type,
            )
            return result.object_name
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MinIO upload failed: {e}",
            )

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        try:
            return self.client.presigned_get_object(
                settings.MINIO_BUCKET,
                object_name,
                expires=expires,
            )
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MinIO presigned URL failed: {e}",
            )

    def download_file(self, object_name: str, file_path: str) -> None:
        try:
            self.client.fget_object(settings.MINIO_BUCKET, object_name, file_path)
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MinIO download failed: {e}",
            )

    def delete_object(self, object_name: str) -> None:
        try:
            self.client.remove_object(settings.MINIO_BUCKET, object_name)
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MinIO delete failed: {e}",
            )

    def get_object(self, object_name: str) -> Any:
        try:
            return self.client.get_object(settings.MINIO_BUCKET, object_name)
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MinIO get object failed: {e}",
            )


minio_client = MinioClientWrapper()
