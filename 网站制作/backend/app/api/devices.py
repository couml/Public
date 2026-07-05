import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.printer import Printer
from app.models.printer_alert import PrinterAlert
from app.models.printer_status_log import PrinterStatusLog
from app.models.print_job import PrintJob
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.device import (
    PrinterAlertOut,
    PrinterListQuery,
    PrinterOut,
    PrinterStatsOut,
    PrinterStatusOut,
)

router = APIRouter(prefix="/devices")


@router.get("", response_model=PaginatedResponse[PrinterOut])
async def list_printers(
    brand: str | None = Query(default=None, description="Filter by brand"),
    status: str | None = Query(default=None, description="Filter by status"),
    search: str | None = Query(default=None, description="Search keyword"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """List printers with optional filters and pagination."""
    query = select(Printer)

    if brand:
        query = query.where(Printer.brand == brand)
    if status:
        query = query.where(Printer.status == status)
    if search:
        query = query.where(
            (Printer.name.ilike(f"%{search}%"))
            | (Printer.model.ilike(f"%{search}%"))
            | (Printer.location.ilike(f"%{search}%"))
        )

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=items,
        total=len(items),  # simplified; ideally run count query
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.get("/{id}", response_model=PrinterOut)
async def get_printer(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get printer detail by ID."""
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

    return printer


@router.get("/{id}/logs", response_model=PaginatedResponse[PrinterStatusOut])
async def get_printer_logs(
    id: str,
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """Get status logs for a printer."""
    try:
        printer_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid printer ID format",
        )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = await db.execute(
        select(PrinterStatusLog)
        .where(
            PrinterStatusLog.printer_id == printer_id,
            PrinterStatusLog.recorded_at >= cutoff,
        )
        .order_by(PrinterStatusLog.recorded_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()

    return PaginatedResponse(
        items=logs,
        total=len(logs),
        page=1,
        page_size=limit,
        total_pages=1,
    )


@router.get("/{id}/alerts", response_model=PaginatedResponse[PrinterAlertOut])
async def get_printer_alerts(
    id: str,
    resolved: bool = Query(default=False, description="Include resolved alerts"),
    db: AsyncSession = Depends(get_db),
):
    """Get alerts for a printer."""
    try:
        printer_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid printer ID format",
        )

    query = select(PrinterAlert).where(PrinterAlert.printer_id == printer_id)
    if not resolved:
        query = query.where(PrinterAlert.is_resolved == False)  # noqa: E712

    query = query.order_by(PrinterAlert.created_at.desc())

    result = await db.execute(query)
    alerts = result.scalars().all()

    return PaginatedResponse(
        items=alerts,
        total=len(alerts),
        page=1,
        page_size=100,
        total_pages=1,
    )


@router.post("/{id}/alerts/{alert_id}/resolve")
async def resolve_alert(
    id: str,
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert as resolved."""
    try:
        printer_id = uuid.UUID(id)
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    result = await db.execute(
        select(PrinterAlert).where(
            PrinterAlert.id == alert_uuid,
            PrinterAlert.printer_id == printer_id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    if alert.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alert already resolved",
        )

    alert.is_resolved = True
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    return {"success": True, "message": "Alert resolved"}


@router.get("/{id}/stats", response_model=PrinterStatsOut)
async def get_printer_stats(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get print statistics for a printer (mock data)."""
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

    import random

    return PrinterStatsOut(
        total_pages=printer.total_pages_printed,
        pages_today=random.randint(10, 500),
        pages_this_week=random.randint(100, 3000),
        pages_this_month=random.randint(500, 12000),
        total_errors=random.randint(0, 50),
        uptime_percentage=round(random.uniform(90.0, 99.9), 1),
    )


@router.get("/{id}/queue", response_model=PaginatedResponse)
async def get_printer_queue(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get current print queue for a printer."""
    try:
        printer_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid printer ID format",
        )

    result = await db.execute(
        select(PrintJob)
        .where(
            PrintJob.printer_id == printer_id,
            PrintJob.status.in_(["queued", "waiting", "printing"]),
        )
        .order_by(PrintJob.queued_at.asc())
    )
    jobs = result.scalars().all()

    return PaginatedResponse(
        items=jobs,
        total=len(jobs),
        page=1,
        page_size=100,
        total_pages=1,
    )
