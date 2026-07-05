from __future__ import annotations
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class UploadInitRequest(ORMModel):
    filename: str
    file_size: int
    file_md5: str
    total_chunks: int
    mime_type: str | None = None


class UploadInitResponse(ORMModel):
    upload_id: str
    file_id: str


class UploadCompleteRequest(ORMModel):
    upload_id: str
    file_id: str


class FileRecordOut(ORMModel):
    id: UUID
    user_id: UUID
    original_filename: str
    file_size: int
    mime_type: str | None = None
    file_md5: str | None = None
    storage_path: str
    status: str
    converted_format: str | None = None
    converted_path: str | None = None
    page_count: int | None = None
    is_temporary: bool = False
    expires_at: datetime | None = None
    created_at: datetime


class ConvertRequest(ORMModel):
    file_id: str
    target_format: str


class StagingFileOut(ORMModel):
    id: UUID
    user_id: UUID
    original_filename: str
    file_size: int
    mime_type: str | None = None
    status: str
    is_temporary: bool = False
    expires_at: datetime | None = None
    created_at: datetime
