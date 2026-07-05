from __future__ import annotations

from typing import Optional
import asyncio
import os
import secrets
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.scan_document import ScanDocument
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.document import DocumentOut, ShareResponse, TagUpdate
from app.utils.minio_client import minio_client

router = APIRouter(prefix="/documents")


@router.get("", response_model=PaginatedResponse[DocumentOut])
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's documents with optional category/tag filters."""
    query = select(ScanDocument).where(ScanDocument.user_id == current_user.id)

    if category:
        query = query.where(ScanDocument.category == category)

    query = query.order_by(ScanDocument.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    docs = result.scalars().all()

    # Filter by tag in Python (JSONB containment is PostgreSQL-specific)
    if tag:
        docs = [d for d in docs if d.tags and tag in d.tags]

    return PaginatedResponse(
        items=docs,
        total=len(docs),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.get("/{id}", response_model=DocumentOut)
async def get_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document detail."""
    try:
        doc_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format",
        )

    result = await db.execute(
        select(ScanDocument).where(
            ScanDocument.id == doc_id,
            ScanDocument.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return doc


@router.get("/{id}/download")
async def download_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream document from MinIO for download."""
    try:
        doc_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format",
        )

    result = await db.execute(
        select(ScanDocument).where(
            ScanDocument.id == doc_id,
            ScanDocument.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    tmp_path = tempfile.mktemp()
    try:
        minio_client.download_file(doc.storage_path, tmp_path)

        def iterfile():
            with open(tmp_path, "rb") as f:
                yield from f
            os.unlink(tmp_path)

        return StreamingResponse(
            iterfile(),
            media_type=doc.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{doc.filename}"'
            },
        )
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


@router.post("/{id}/ocr")
async def trigger_ocr(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger OCR processing (simulated)."""
    try:
        doc_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format",
        )

    result = await db.execute(
        select(ScanDocument).where(
            ScanDocument.id == doc_id,
            ScanDocument.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Set status to processing
    doc.ocr_status = "processing"
    await db.commit()

    # Simulate OCR processing
    await asyncio.sleep(3)

    # Mock OCR result
    mock_ocr_text = (
        "【OCR识别结果】\n\n"
        "这是一份扫描文档的模拟OCR识别文本。\n"
        "实际应用中，这里会包含从扫描图像中提取的全部文字内容。\n\n"
        "文档元数据：\n"
        f"文件名：{doc.filename}\n"
        f"页数：{doc.page_count or 1}\n"
        f"识别时间：{datetime.now(timezone.utc).isoformat()}\n"
    )

    doc.ocr_status = "completed"
    doc.ocr_text = mock_ocr_text
    await db.commit()
    await db.refresh(doc)

    return {
        "success": True,
        "status": "completed",
        "ocr_text": mock_ocr_text,
    }


@router.post("/{id}/share", response_model=ShareResponse)
async def share_document(
    id: str,
    expires_hours: int = Query(default=24, ge=1, le=8760),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a share token for a document."""
    try:
        doc_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format",
        )

    result = await db.execute(
        select(ScanDocument).where(
            ScanDocument.id == doc_id,
            ScanDocument.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Generate share token
    token = secrets.token_hex(16)  # 32-char hex string
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

    doc.share_token = token
    doc.share_expires_at = expires_at
    doc.is_shared = True
    await db.commit()

    share_url = f"/api/v1/documents/shared/{token}"

    return ShareResponse(
        share_url=share_url,
        share_token=token,
        expires_at=expires_at.isoformat(),
    )


@router.put("/{id}/tags", response_model=DocumentOut)
async def update_tags(
    id: str,
    body: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update tags and category of a document."""
    try:
        doc_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format",
        )

    result = await db.execute(
        select(ScanDocument).where(
            ScanDocument.id == doc_id,
            ScanDocument.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    doc.tags = body.tags
    if body.category is not None:
        doc.category = body.category
    await db.commit()
    await db.refresh(doc)

    return doc


@router.get("/shared/{token}", response_model=DocumentOut)
async def access_shared_document(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Access a shared document by token (no auth required)."""
    result = await db.execute(
        select(ScanDocument).where(ScanDocument.share_token == token)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or invalid share link",
        )

    # Validate expiry
    if doc.share_expires_at and doc.share_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired",
        )

    return doc
