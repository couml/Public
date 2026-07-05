import asyncio
import random
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ScanDocument


async def list_documents(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: str | None = None,
    tag: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ScanDocument], int]:
    conditions = [ScanDocument.user_id == user_id]
    if category:
        conditions.append(ScanDocument.category == category)
    # For JSONB tag filtering, use PostgreSQL containment operator
    if tag:
        conditions.append(
            func.jsonb_path_exists(
                ScanDocument.tags, f'$[*] ? (@ == "{tag}")'
            )
        )

    base_query = select(ScanDocument).where(and_(*conditions))

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        base_query
        .order_by(ScanDocument.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    documents = list(result.scalars().all())

    return documents, total


async def get_document_by_id(
    db: AsyncSession, document_id: uuid.UUID
) -> ScanDocument:
    result = await db.execute(
        select(ScanDocument).where(ScanDocument.id == document_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


async def trigger_ocr(
    db: AsyncSession, document_id: uuid.UUID
) -> ScanDocument:
    result = await db.execute(
        select(ScanDocument).where(ScanDocument.id == document_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.ocr_status = "processing"
    await db.commit()

    # Simulate OCR processing time
    await asyncio.sleep(random.uniform(2.0, 3.0))

    document.ocr_text = (
        "【模拟OCR识别文本】\n\n"
        "这是一份扫描文档的OCR识别结果示例。\n"
        "实际部署时将由Tesseract或PaddleOCR等引擎处理。\n\n"
        "文档包含以下内容：\n"
        "1. 章节标题自动识别\n"
        "2. 正文内容提取\n"
        "3. 关键词标注\n"
        "4. 表格数据识别（如适用）\n\n"
        "--- 第1页 ---\n"
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
        "--- 第2页 ---\n"
        "打印机维护记录表\n"
        "日期 | 维护项目 | 操作员 | 备注\n"
        "2025-01-15 | 硒鼓更换 | 张三 | W1360A标准容量\n"
        "2025-03-22 | 定影组件检查 | 李四 | 运行正常\n\n"
        "--- 识别结束 ---"
    )
    document.ocr_status = "completed"
    document.page_count = random.randint(1, 15)
    await db.commit()
    await db.refresh(document)

    return document


async def generate_share_token(
    db: AsyncSession,
    document_id: uuid.UUID,
    expires_hours: int = 24,
) -> dict:
    result = await db.execute(
        select(ScanDocument).where(ScanDocument.id == document_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    token = secrets.token_hex(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

    document.share_token = token
    document.share_expires_at = expires_at
    document.is_shared = True
    await db.commit()
    await db.refresh(document)

    return {
        "share_url": f"/api/v1/documents/shared/{token}",
        "token": token,
        "expires_at": expires_at.isoformat(),
        "document_id": str(document_id),
    }


async def get_shared_document(
    db: AsyncSession, token: str
) -> ScanDocument:
    result = await db.execute(
        select(ScanDocument).where(ScanDocument.share_token == token)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Shared document not found")

    if document.share_expires_at and document.share_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=410, detail="Share link has expired"
        )

    return document


async def update_tags(
    db: AsyncSession,
    document_id: uuid.UUID,
    tags: list[str] | None = None,
    category: str | None = None,
) -> ScanDocument:
    result = await db.execute(
        select(ScanDocument).where(ScanDocument.id == document_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if tags is not None:
        document.tags = tags
    if category is not None:
        document.category = category

    await db.commit()
    await db.refresh(document)
    return document
