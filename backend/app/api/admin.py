from __future__ import annotations

from typing import Optional
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.driver_package import DriverPackage
from app.models.file_record import FileRecord
from app.models.printer import Printer
from app.models.printer_alert import PrinterAlert
from app.models.print_job import PrintJob
from app.models.system_log import SystemLog
from app.models.user import User
from app.schemas.admin import AdminLogOut, AdminStatsOut
from app.schemas.common import PaginatedResponse
from app.schemas.device import PrinterOut
from app.schemas.driver import DriverAdminCreate, DriverPackageOut
from app.schemas.user import UserOut, UserUpdate
from app.utils.minio_client import minio_client

router = APIRouter(prefix="/admin")

# All admin routes require admin or it_staff role
admin_required = require_role(["admin", "it_staff"])


async def create_system_log(
    db: AsyncSession,
    user_id: uuid.Optional[UUID],
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    detail: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Helper: create a system log entry."""
    log = SystemLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    await db.commit()


# ---------------------------------------------------------------------------
# Printer admin routes
# ---------------------------------------------------------------------------


@router.get("/printers", response_model=PaginatedResponse[PrinterOut])
async def admin_list_printers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(admin_required),
):
    """Admin: list all printers."""
    query = select(Printer).order_by(Printer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    printers = result.scalars().all()

    return PaginatedResponse(
        items=printers,
        total=len(printers),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.post("/printers", response_model=PrinterOut, status_code=status.HTTP_201_CREATED)
async def admin_add_printer(
    name: str = Form(...),
    brand: str = Form(...),
    model: str = Form(...),
    ip_address: str = Form(...),
    location: Optional[str] = Form(default=None),
    serial_number: Optional[str] = Form(default=None),
    mac_address: Optional[str] = Form(default=None),
    supports_color: bool = Form(default=False),
    supports_duplex: bool = Form(default=False),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin: add a new printer."""
    printer = Printer(
        name=name,
        brand=brand,
        model=model,
        ip_address=ip_address,
        location=location,
        serial_number=serial_number,
        mac_address=mac_address,
        supports_color=supports_color,
        supports_duplex=supports_duplex,
        status="offline",
    )
    db.add(printer)
    await db.commit()
    await db.refresh(printer)

    await create_system_log(
        db,
        current_user.id,
        action="create",
        resource="printer",
        resource_id=str(printer.id),
        detail={"name": name, "brand": brand, "model": model},
    )

    return printer


@router.put("/printers/{id}", response_model=PrinterOut)
async def admin_update_printer(
    id: str,
    name: Optional[str] = Form(default=None),
    location: Optional[str] = Form(default=None),
    ip_address: Optional[str] = Form(default=None),
    snmp_community: Optional[str] = Form(default=None),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin: update printer configuration."""
    try:
        printer_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid printer ID format",
        )

    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()

    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    if name is not None:
        printer.name = name
    if location is not None:
        printer.location = location
    if ip_address is not None:
        printer.ip_address = ip_address
    if snmp_community is not None:
        printer.snmp_community = snmp_community

    printer.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(printer)

    await create_system_log(
        db,
        current_user.id,
        action="update",
        resource="printer",
        resource_id=str(printer.id),
        detail={"name": printer.name},
    )

    return printer


@router.delete("/printers/{id}")
async def admin_delete_printer(
    id: str,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin: delete a printer."""
    try:
        printer_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid printer ID format",
        )

    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()

    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    await db.delete(printer)
    await db.commit()

    await create_system_log(
        db,
        current_user.id,
        action="delete",
        resource="printer",
        resource_id=str(printer_id),
        detail={"name": printer.name},
    )

    return {"success": True, "message": "Printer deleted"}


# ---------------------------------------------------------------------------
# Driver admin routes
# ---------------------------------------------------------------------------


@router.get("/drivers", response_model=PaginatedResponse[DriverPackageOut])
async def admin_list_drivers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(admin_required),
):
    """Admin: list all driver packages."""
    query = select(DriverPackage).order_by(DriverPackage.created_at.desc())
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


@router.post("/drivers", response_model=DriverPackageOut, status_code=status.HTTP_201_CREATED)
async def admin_add_driver(
    driver_file: UploadFile = File(...),
    brand: str = Form(...),
    model: str = Form(...),
    os_platform: str = Form(...),
    version: str = Form(...),
    release_date: str = Form(...),
    changelog: Optional[str] = Form(default=None),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin: upload a new driver package."""
    # Save uploaded file to MinIO
    file_ext = driver_file.filename.rsplit(".", 1)[-1].lower() if "." in (driver_file.filename or "") else "zip"
    storage_filename = f"drivers/{brand}/{model}/{version}/{uuid.uuid4()}.{file_ext}"

    import os
    import tempfile

    content = await driver_file.read()
    file_size = len(content)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        minio_client.upload_file(storage_filename, tmp_path, "application/octet-stream")
    finally:
        os.unlink(tmp_path)

    # Create driver record
    driver = DriverPackage(
        brand=brand,
        model=model,
        os_platform=os_platform,
        version=version,
        file_size=file_size,
        storage_path=storage_filename,
        release_date=datetime.fromisoformat(release_date).date() if release_date else datetime.now(timezone.utc).date(),
        changelog=changelog,
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)

    await create_system_log(
        db,
        current_user.id,
        action="create",
        resource="driver",
        resource_id=str(driver.id),
        detail={"brand": brand, "model": model, "version": version},
    )

    return driver


@router.put("/drivers/{id}", response_model=DriverPackageOut)
async def admin_update_driver(
    id: str,
    brand: Optional[str] = Form(default=None),
    model: Optional[str] = Form(default=None),
    version: Optional[str] = Form(default=None),
    changelog: Optional[str] = Form(default=None),
    is_active: Optional[bool] = Form(default=None),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin: update driver metadata."""
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

    if brand is not None:
        driver.brand = brand
    if model is not None:
        driver.model = model
    if version is not None:
        driver.version = version
    if changelog is not None:
        driver.changelog = changelog
    if is_active is not None:
        driver.is_active = is_active

    await db.commit()
    await db.refresh(driver)

    await create_system_log(
        db,
        current_user.id,
        action="update",
        resource="driver",
        resource_id=str(driver.id),
    )

    return driver


@router.delete("/drivers/{id}")
async def admin_delete_driver(
    id: str,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin: delete/deactivate a driver."""
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

    # Soft deactivate instead of hard delete
    driver.is_active = False
    await db.commit()

    await create_system_log(
        db,
        current_user.id,
        action="deactivate",
        resource="driver",
        resource_id=str(driver_id),
    )

    return {"success": True, "message": "Driver deactivated"}


# ---------------------------------------------------------------------------
# User admin routes
# ---------------------------------------------------------------------------


@router.get("/users", response_model=PaginatedResponse[UserOut])
async def admin_list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(admin_required),
):
    """Admin: list all users with filters."""
    query = select(User)

    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return PaginatedResponse(
        items=users,
        total=len(users),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.put("/users/{id}", response_model=UserOut)
async def admin_update_user(
    id: str,
    body: UserUpdate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin: update user role or activation status."""
    try:
        user_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.department is not None:
        user.department = body.department
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)

    await create_system_log(
        db,
        current_user.id,
        action="update",
        resource="user",
        resource_id=str(user.id),
    )

    return user


@router.delete("/users/{id}")
async def admin_deactivate_user(
    id: str,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin: deactivate a user (soft delete)."""
    try:
        user_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    user.is_active = False
    await db.commit()

    await create_system_log(
        db,
        current_user.id,
        action="deactivate",
        resource="user",
        resource_id=str(user_id),
    )

    return {"success": True, "message": "User deactivated"}


# ---------------------------------------------------------------------------
# System logs and stats
# ---------------------------------------------------------------------------


@router.get("/logs", response_model=PaginatedResponse[AdminLogOut])
async def admin_list_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    action: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(admin_required),
):
    """Admin: list system activity logs."""
    query = select(SystemLog)

    if action:
        query = query.where(SystemLog.action == action)
    if user_id:
        try:
            uid = uuid.UUID(user_id)
            query = query.where(SystemLog.user_id == uid)
        except ValueError:
            pass

    query = query.order_by(SystemLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return PaginatedResponse(
        items=logs,
        total=len(logs),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.get("/stats", response_model=AdminStatsOut)
async def admin_get_stats(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(admin_required),
):
    """Admin: system-wide statistics."""
    # Count users
    user_result = await db.execute(select(func.count(User.id)))
    total_users = user_result.scalar() or 0

    # Count printers
    printer_result = await db.execute(select(func.count(Printer.id)))
    total_printers = printer_result.scalar() or 0

    # Count jobs today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    jobs_result = await db.execute(
        select(func.count(PrintJob.id)).where(PrintJob.created_at >= today_start)
    )
    total_jobs_today = jobs_result.scalar() or 0

    # Estimate storage (sum of file sizes)
    storage_result = await db.execute(select(func.sum(FileRecord.file_size)))
    total_storage = storage_result.scalar() or 0

    # Active alerts
    alerts_result = await db.execute(
        select(func.count(PrinterAlert.id)).where(
            PrinterAlert.is_resolved == False  # noqa: E712
        )
    )
    active_alerts = alerts_result.scalar() or 0

    # Recent logs
    logs_result = await db.execute(
        select(SystemLog)
        .order_by(SystemLog.created_at.desc())
        .limit(10)
    )
    recent_logs = logs_result.scalars().all()

    return AdminStatsOut(
        total_users=total_users,
        total_printers=total_printers,
        total_jobs_today=total_jobs_today,
        total_storage_bytes=total_storage,
        active_alerts=active_alerts,
        recent_logs=recent_logs,
    )
