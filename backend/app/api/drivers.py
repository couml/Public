import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from redis import Redis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.driver_download_log import DriverDownloadLog
from app.models.driver_package import DriverPackage
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.driver import DriverListQuery, DriverPackageOut, HP136aPageOut
from app.utils.minio_client import minio_client
from app.utils.redis_client import get_redis
from app.core.config import settings

router = APIRouter(prefix="/drivers")


@router.get("", response_model=PaginatedResponse[DriverPackageOut])
async def list_drivers(
    brand: str | None = Query(default=None),
    model: str | None = Query(default=None),
    os: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List driver packages with filters and pagination."""
    query = select(DriverPackage).where(DriverPackage.is_active == True)  # noqa: E712

    if brand:
        query = query.where(DriverPackage.brand == brand)
    if model:
        query = query.where(DriverPackage.model == model)
    if os:
        query = query.where(DriverPackage.os_platform == os)
    if search:
        query = query.where(
            (DriverPackage.brand.ilike(f"%{search}%"))
            | (DriverPackage.model.ilike(f"%{search}%"))
            | (DriverPackage.version.ilike(f"%{search}%"))
        )

    query = query.order_by(DriverPackage.release_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    drivers = result.scalars().all()

    return PaginatedResponse(
        items=drivers,
        total=len(drivers),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.get("/brands")
async def list_brands(
    db: AsyncSession = Depends(get_db),
):
    """Return distinct brand names."""
    result = await db.execute(
        select(DriverPackage.brand).distinct().order_by(DriverPackage.brand)
    )
    brands = [row[0] for row in result.all()]
    return {"brands": brands}


@router.get("/models")
async def list_models(
    brand: str = Query(..., description="Brand name"),
    db: AsyncSession = Depends(get_db),
):
    """Return distinct models for a given brand."""
    result = await db.execute(
        select(DriverPackage.model)
        .where(DriverPackage.brand == brand)
        .distinct()
        .order_by(DriverPackage.model)
    )
    models = [row[0] for row in result.all()]
    return {"brand": brand, "models": models}


@router.get("/hp-136a", response_model=HP136aPageOut)
async def get_hp_136a_page(
    db: AsyncSession = Depends(get_db),
):
    """Return HP 136a dedicated page data (mock manuals, FAQs, install guides)."""
    # Get HP 136a drivers
    result = await db.execute(
        select(DriverPackage)
        .where(
            DriverPackage.brand == "HP",
            DriverPackage.model == "Laser 136a",
            DriverPackage.is_active == True,  # noqa: E712
        )
        .order_by(DriverPackage.release_date.desc())
    )
    drivers = result.scalars().all()

    manuals = [
        {"title": "HP Laser 136a 用户手册", "url": "#", "pages": 120, "language": "zh"},
        {"title": "HP Laser 136a Quick Start Guide", "url": "#", "pages": 8, "language": "en"},
        {"title": "HP Laser 136a 安装指南", "url": "#", "pages": 24, "language": "zh"},
    ]

    faqs = [
        {"question": "如何安装HP 136a驱动？", "answer": "请下载对应操作系统的驱动包，运行安装程序并按照向导完成安装。"},
        {"question": "打印机显示离线怎么办？", "answer": "检查USB连接或网络连接，确保打印机电源已打开。重新启动打印机和电脑后重试。"},
        {"question": "如何更换硒鼓？", "answer": "打开前盖，取出旧硒鼓，安装新硒鼓并合上前盖。建议使用HP原装136a硒鼓。"},
        {"question": "打印出现条纹怎么办？", "answer": "清洁打印头或更换硒鼓。在打印机设置中运行清洁页面。"},
    ]

    install_guides = {
        "windows": {
            "title": "Windows 安装指南",
            "steps": [
                "从上方下载对应Windows版本的驱动程序",
                "运行下载的.exe安装文件",
                "选择USB或网络连接方式",
                "按照向导完成安装并打印测试页",
            ],
        },
        "macos": {
            "title": "macOS 安装指南",
            "steps": [
                "下载macOS版驱动程序",
                "打开.dmg文件并运行安装包",
                "在系统偏好设置中添加打印机",
                "选择HP Laser 136a并完成设置",
            ],
        },
    }

    return HP136aPageOut(
        drivers=drivers,
        manuals=manuals,
        faqs=faqs,
        install_guides=install_guides,
    )


@router.get("/{id}", response_model=DriverPackageOut)
async def get_driver(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get driver detail."""
    try:
        driver_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid driver ID format",
        )

    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == driver_id)
    )
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    return driver


@router.get("/{id}/download")
async def download_driver(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """Increment download count, log download, stream file."""
    try:
        driver_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid driver ID format",
        )

    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == driver_id)
    )
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Increment download count
    driver.download_count += 1

    # Log download
    log = DriverDownloadLog(
        user_id=current_user.id if current_user else None,
        driver_id=driver_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(log)
    await db.commit()

    # Stream from MinIO
    import tempfile
    import os

    tmp_path = tempfile.mktemp()
    try:
        minio_client.download_file(driver.storage_path, tmp_path)

        filename = f"{driver.brand}_{driver.model}_{driver.version}.zip"

        def iterfile():
            with open(tmp_path, "rb") as f:
                yield from f
            os.unlink(tmp_path)

        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


@router.get("/{id}/versions")
async def get_driver_versions(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return all versions for the same brand+model combination."""
    try:
        driver_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid driver ID format",
        )

    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == driver_id)
    )
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Get all versions for same brand+model
    result = await db.execute(
        select(DriverPackage)
        .where(
            DriverPackage.brand == driver.brand,
            DriverPackage.model == driver.model,
            DriverPackage.is_active == True,  # noqa: E712
        )
        .order_by(DriverPackage.release_date.desc())
    )
    versions = result.scalars().all()

    return versions
