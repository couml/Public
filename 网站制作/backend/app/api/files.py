import asyncio
import hashlib
import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.file_record import FileRecord
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.file import (
    ConvertRequest,
    FileRecordOut,
    StagingFileOut,
    UploadCompleteRequest,
    UploadInitRequest,
    UploadInitResponse,
)
from app.utils.minio_client import minio_client
from app.utils.redis_client import get_redis
from app.core.config import settings

router = APIRouter(prefix="/files")


@router.post("/upload/init", response_model=UploadInitResponse)
async def upload_init(
    body: UploadInitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Initialize a chunked upload session."""
    upload_id = str(uuid.uuid4())

    # Create file record with status 'uploading'
    ext = body.filename.rsplit(".", 1)[-1].lower() if "." in body.filename else "bin"
    stored_filename = f"{uuid.uuid4()}.{ext}"
    storage_path = f"files/{current_user.id}/{stored_filename}"

    file_record = FileRecord(
        user_id=current_user.id,
        original_filename=body.filename,
        stored_filename=stored_filename,
        file_size=body.file_size,
        mime_type=body.mime_type or "application/octet-stream",
        file_md5=body.file_md5,
        storage_path=storage_path,
        chunk_count=body.total_chunks,
        status="uploading",
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    # Store chunk tracking in Redis
    redis.hset(f"upload:{upload_id}", "total_chunks", body.total_chunks)
    redis.hset(f"upload:{upload_id}", "received_chunks", 0)
    redis.hset(f"upload:{upload_id}", "file_id", str(file_record.id))
    redis.hset(f"upload:{upload_id}", "file_md5", body.file_md5)
    redis.expire(f"upload:{upload_id}", 3600)  # 1 hour TTL

    return UploadInitResponse(upload_id=upload_id, file_id=str(file_record.id))


@router.put("/upload/chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    upload_id: str = Query(..., description="Upload session ID"),
    chunk_index: int = Query(..., ge=0, description="Chunk index (0-based)"),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Upload a single chunk to MinIO."""
    # Verify upload session exists
    total_chunks = redis.hget(f"upload:{upload_id}", "total_chunks")
    if not total_chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found or expired",
        )

    # Save chunk to MinIO
    chunk_object = f"chunks/{upload_id}/{chunk_index}"
    chunk_data = await chunk.read()

    # Write chunk to temp file for MinIO upload
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(chunk_data)
        tmp_path = tmp.name

    try:
        minio_client.upload_file(chunk_object, tmp_path, "application/octet-stream")
    finally:
        os.unlink(tmp_path)

    # Update Redis: add chunk_index to received_chunks set
    redis.sadd(f"upload:{upload_id}:received", str(chunk_index))
    redis.expire(f"upload:{upload_id}", 3600)

    return {"success": True, "chunk_index": chunk_index}


@router.post("/upload/complete")
async def upload_complete(
    body: UploadCompleteRequest,
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complete a chunked upload: merge chunks, verify MD5, finalize."""
    # Verify upload session
    total_chunks = redis.hget(f"upload:{body.upload_id}", "total_chunks")
    if not total_chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found or expired",
        )

    total = int(total_chunks)
    received = redis.smembers(f"upload:{body.upload_id}:received")

    if len(received) != total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not all chunks received ({len(received)}/{total})",
        )

    # Get file record
    try:
        file_id = uuid.UUID(body.file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format",
        )

    result = await db.execute(select(FileRecord).where(FileRecord.id == file_id))
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File record not found",
        )

    # Merge chunks from MinIO
    merged_data = bytearray()
    for i in range(total):
        chunk_object = f"chunks/{body.upload_id}/{i}"
        try:
            response = minio_client.get_object(chunk_object)
            merged_data.extend(response.read())
            response.close()
            response.release_conn()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read chunk {i}",
            )

    # Compute MD5 of merged file
    computed_md5 = hashlib.md5(merged_data).hexdigest()
    declared_md5 = redis.hget(f"upload:{body.upload_id}", "file_md5")

    if computed_md5 != declared_md5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MD5 checksum mismatch",
        )

    # Upload final merged file to MinIO
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(merged_data)
        tmp_path = tmp.name

    try:
        minio_client.upload_file(
            file_record.storage_path,
            tmp_path,
            file_record.mime_type or "application/octet-stream",
        )
    finally:
        os.unlink(tmp_path)

    # Update file record status
    file_record.status = "uploaded"
    file_record.file_size = len(merged_data)
    await db.commit()
    await db.refresh(file_record)

    # Cleanup chunks from MinIO and Redis
    for i in range(total):
        try:
            minio_client.delete_object(f"chunks/{body.upload_id}/{i}")
        except Exception:
            pass  # Best-effort cleanup

    redis.delete(f"upload:{body.upload_id}")
    redis.delete(f"upload:{body.upload_id}:received")

    return FileRecordOut.model_validate(file_record)


@router.get("/", response_model=PaginatedResponse[FileRecordOut])
async def list_files(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's files."""
    query = select(FileRecord).where(FileRecord.user_id == current_user.id)

    if status_filter:
        query = query.where(FileRecord.status == status_filter)

    query = query.order_by(FileRecord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    files = result.scalars().all()

    return PaginatedResponse(
        items=files,
        total=len(files),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.get("/{id}", response_model=FileRecordOut)
async def get_file(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get file metadata."""
    try:
        file_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format",
        )

    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.user_id == current_user.id,
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return file_record


@router.get("/{id}/preview")
async def preview_file(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a presigned URL for file preview."""
    try:
        file_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format",
        )

    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.user_id == current_user.id,
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    presigned_url = minio_client.get_presigned_url(file_record.storage_path, expires=3600)
    return {"url": presigned_url}


@router.get("/{id}/download")
async def download_file(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream file from MinIO for download."""
    try:
        file_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format",
        )

    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.user_id == current_user.id,
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Download to temp file and stream
    tmp_path = tempfile.mktemp()
    try:
        minio_client.download_file(file_record.storage_path, tmp_path)

        def iterfile():
            with open(tmp_path, "rb") as f:
                yield from f
            os.unlink(tmp_path)

        return StreamingResponse(
            iterfile(),
            media_type=file_record.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file_record.original_filename}"'
            },
        )
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


@router.delete("/{id}")
async def delete_file(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete file from MinIO and database."""
    try:
        file_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format",
        )

    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.user_id == current_user.id,
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Delete from MinIO
    try:
        minio_client.delete_object(file_record.storage_path)
    except Exception:
        pass  # Best-effort

    # Delete from DB
    await db.delete(file_record)
    await db.commit()

    return {"success": True, "message": "File deleted"}


@router.post("/convert", response_model=FileRecordOut)
async def convert_file(
    body: ConvertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert file to target format (simulated)."""
    try:
        file_id = uuid.UUID(body.file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format",
        )

    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.user_id == current_user.id,
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Set status to converting
    file_record.status = "converting"
    await db.commit()

    # Simulate conversion delay
    await asyncio.sleep(3)  # 2-4 seconds simulation

    # Set as converted
    file_record.status = "converted"
    file_record.converted_format = body.target_format
    file_record.converted_path = f"{file_record.storage_path}.{body.target_format}"
    await db.commit()
    await db.refresh(file_record)

    return file_record


@router.get("/staging", response_model=PaginatedResponse[StagingFileOut])
async def list_staging_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List staging files (temporary, not expired, converted)."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(FileRecord).where(
            FileRecord.user_id == current_user.id,
            FileRecord.is_temporary == True,  # noqa: E712
            FileRecord.status == "converted",
            FileRecord.expires_at > now,
        ).order_by(FileRecord.created_at.desc())
    )
    files = result.scalars().all()

    return PaginatedResponse(
        items=files,
        total=len(files),
        page=1,
        page_size=100,
        total_pages=1,
    )
