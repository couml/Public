from __future__ import annotations

from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class UploadInitRequest(ORMModel):
    filename: str
    file_size: int
    file_md5: str
    total_chunks: int
    mime_type: Optional[str] = None


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
    mime_type: Optional[str] = None
    file_md5: Optional[str] = None
    storage_path: str
    status: str
    converted_format: Optional[str] = None
    converted_path: Optional[str] = None
    page_count: Optional[int] = None
    is_temporary: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime


class ConvertRequest(ORMModel):
    file_id: str
    target_format: str


class StagingFileOut(ORMModel):
    id: UUID
    user_id: UUID
    original_filename: str
    file_size: int
    mime_type: Optional[str] = None
    status: str
    is_temporary: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime
