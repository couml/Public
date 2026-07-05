from __future__ import annotations
import asyncio
import hashlib
import os
import random
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FileRecord

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".csv", ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".tiff", ".tif", ".ps", ".pcl", ".prn",
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def _validate_extension(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        raise HTTPException(status_code=400, detail="File has no extension")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed",
        )
    return ext


async def init_upload(
    db: AsyncSession,
    redis,
    user_id: uuid.UUID,
    filename: str,
    file_size: int,
    file_md5: str,
    total_chunks: int,
    mime_type: str | None = None,
) -> tuple[str, uuid.UUID]:
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB",
        )
    _validate_extension(filename)

    upload_id = uuid.uuid4().hex
    file_id = uuid.uuid4()

    file_record = FileRecord(
        id=file_id,
        user_id=user_id,
        original_filename=filename,
        stored_filename=f"{file_id.hex}_{filename}",
        file_size=file_size,
        mime_type=mime_type,
        file_md5=file_md5,
        storage_path=f"files/{user_id}/{file_id}/{filename}",
        chunk_count=total_chunks,
        status="uploading",
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    upload_key = f"upload:{upload_id}"
    await redis.hset(upload_key, mapping={
        "file_id": str(file_id),
        "total_chunks": str(total_chunks),
        "received_chunks": "0",
        "filename": filename,
        "file_size": str(file_size),
    })
    await redis.expire(upload_key, 3600)

    return upload_id, file_id


async def save_chunk(
    minio_client,
    redis,
    upload_id: str,
    chunk_index: int,
    chunk_file: UploadFile,
) -> None:
    upload_key = f"upload:{upload_id}"
    exists = await redis.exists(upload_key)
    if not exists:
        raise HTTPException(status_code=404, detail="Upload session not found")

    chunk_data = await chunk_file.read()
    chunk_path = f"chunks/{upload_id}/{chunk_index}"

    try:
        minio_client.put_object(
            "uploads",
            chunk_path,
            chunk_data,
            len(chunk_data),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save chunk: {str(e)}"
        )

    chunks_key = f"upload:{upload_id}:chunks"
    await redis.sadd(chunks_key, str(chunk_index))
    await redis.expire(chunks_key, 3600)


async def complete_upload(
    db: AsyncSession,
    minio_client,
    redis,
    upload_id: str,
    file_id: uuid.UUID,
) -> FileRecord:
    upload_key = f"upload:{upload_id}"
    chunks_key = f"upload:{upload_id}:chunks"

    meta = await redis.hgetall(upload_key)
    if not meta:
        raise HTTPException(status_code=404, detail="Upload session not found")

    total_chunks = int(meta.get(b"total_chunks", b"0"))
    received_count = await redis.scard(chunks_key)

    if received_count != total_chunks:
        raise HTTPException(
            status_code=400,
            detail=f"Incomplete upload: received {received_count}/{total_chunks} chunks",
        )

    result = await db.execute(
        select(FileRecord).where(FileRecord.id == file_id)
    )
    file_record = result.scalars().first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File record not found")

    # Simulation mode: skip actual chunk merge, just update status
    file_record.status = "uploaded"
    await db.commit()
    await db.refresh(file_record)

    # Cleanup Redis keys
    await redis.delete(upload_key, chunks_key)

    # Cleanup chunks from MinIO (best-effort)
    try:
        objects = list(minio_client.list_objects(
            "uploads", prefix=f"chunks/{upload_id}/", recursive=True,
        ))
        if objects:
            minio_client.remove_objects(
                "uploads",
                [obj.object_name for obj in objects],
            )
    except Exception:
        pass

    return file_record


async def get_staging_files(
    db: AsyncSession, user_id: uuid.UUID
) -> list[FileRecord]:
    result = await db.execute(
        select(FileRecord).where(
            and_(
                FileRecord.user_id == user_id,
                FileRecord.is_temporary == True,
                FileRecord.expires_at > datetime.now(timezone.utc),
                FileRecord.status == "converted",
            )
        ).order_by(FileRecord.created_at.desc())
    )
    return list(result.scalars().all())


async def convert_file(
    db: AsyncSession, file_id: uuid.UUID, target_format: str
) -> FileRecord:
    if target_format not in ("pdf", "pcl", "postscript"):
        raise HTTPException(
            status_code=400,
            detail="target_format must be one of: pdf, pcl, postscript",
        )

    result = await db.execute(
        select(FileRecord).where(FileRecord.id == file_id)
    )
    file_record = result.scalars().first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File record not found")

    file_record.status = "converting"
    file_record.converted_format = target_format
    await db.commit()

    # Simulate conversion delay
    await asyncio.sleep(random.uniform(2.0, 4.0))

    base = os.path.splitext(file_record.original_filename)[0]
    file_record.converted_path = (
        f"files/{file_record.user_id}/{file_id}/{base}.{target_format}"
    )
    file_record.status = "converted"
    await db.commit()
    await db.refresh(file_record)

    return file_record


async def cleanup_expired_files(
    db: AsyncSession, minio_client
) -> int:
    result = await db.execute(
        select(FileRecord).where(
            and_(
                FileRecord.is_temporary == True,
                FileRecord.expires_at < datetime.now(timezone.utc),
            )
        )
    )
    expired = list(result.scalars().all())

    count = 0
    for record in expired:
        # Delete from MinIO
        try:
            minio_client.remove_object("uploads", record.storage_path)
        except Exception:
            pass
        if record.converted_path:
            try:
                minio_client.remove_object("uploads", record.converted_path)
            except Exception:
                pass
        await db.delete(record)
        count += 1

    await db.commit()
    return count
