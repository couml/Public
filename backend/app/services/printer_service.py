from __future__ import annotations
import random
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Printer, PrinterAlert, PrinterStatusLog, PrintJob


async def get_printers(
    db: AsyncSession,
    brand: str | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Printer], int]:
    conditions = []
    if brand:
        conditions.append(Printer.brand == brand)
    if status:
        conditions.append(Printer.status == status)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            or_(
                Printer.name.ilike(pattern),
                Printer.brand.ilike(pattern),
                Printer.model.ilike(pattern),
                Printer.ip_address.ilike(pattern),
                Printer.location.ilike(pattern),
            )
        )

    base_query = select(Printer)
    if conditions:
        base_query = base_query.where(and_(*conditions))

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        base_query
        .order_by(Printer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    printers = list(result.scalars().all())

    return printers, total


async def get_printer_by_id(db: AsyncSession, printer_id: uuid.UUID) -> Printer:
    result = await db.execute(
        select(Printer).where(Printer.id == printer_id)
    )
    printer = result.scalars().first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printer


async def get_printer_logs(
    db: AsyncSession,
    printer_id: uuid.UUID,
    hours: int = 24,
    limit: int = 100,
) -> list[PrinterStatusLog]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(PrinterStatusLog)
        .where(
            and_(
                PrinterStatusLog.printer_id == printer_id,
                PrinterStatusLog.recorded_at >= cutoff,
            )
        )
        .order_by(PrinterStatusLog.recorded_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_printer_alerts(
    db: AsyncSession,
    printer_id: uuid.UUID,
    resolved: bool = False,
) -> list[PrinterAlert]:
    result = await db.execute(
        select(PrinterAlert)
        .where(
            and_(
                PrinterAlert.printer_id == printer_id,
                PrinterAlert.is_resolved == resolved,
            )
        )
        .order_by(PrinterAlert.created_at.desc())
    )
    return list(result.scalars().all())


async def resolve_alert(
    db: AsyncSession, alert_id: uuid.UUID, user_id: uuid.UUID
) -> PrinterAlert:
    result = await db.execute(
        select(PrinterAlert).where(PrinterAlert.id == alert_id)
    )
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    alert.resolved_by = user_id
    alert.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)
    return alert


async def get_printer_stats(
    db: AsyncSession, printer_id: uuid.UUID
) -> dict:
    await get_printer_by_id(db, printer_id)

    return {
        "printer_id": str(printer_id),
        "pages_today": random.randint(10, 500),
        "pages_this_week": random.randint(100, 3000),
        "pages_this_month": random.randint(500, 12000),
        "error_count": random.randint(0, 15),
        "uptime_percent": round(random.uniform(85.0, 99.9), 1),
        "avg_response_time_ms": random.randint(20, 300),
        "toner_remaining_pages_est": random.randint(0, 5000),
    }


async def get_printer_queue(
    db: AsyncSession, printer_id: uuid.UUID
) -> list[PrintJob]:
    await get_printer_by_id(db, printer_id)

    result = await db.execute(
        select(PrintJob)
        .where(
            and_(
                PrintJob.printer_id == printer_id,
                PrintJob.status.in_(["queued", "waiting", "printing"]),
            )
        )
        .order_by(PrintJob.queued_at.asc())
    )
    return list(result.scalars().all())


async def create_printer(
    db: AsyncSession, printer_data: dict
) -> Printer:
    printer = Printer(**printer_data)
    db.add(printer)
    await db.commit()
    await db.refresh(printer)
    return printer


async def update_printer(
    db: AsyncSession, printer_id: uuid.UUID, printer_data: dict
) -> Printer:
    printer = await get_printer_by_id(db, printer_id)
    for key, value in printer_data.items():
        if hasattr(printer, key):
            setattr(printer, key, value)
    await db.commit()
    await db.refresh(printer)
    return printer


async def delete_printer(
    db: AsyncSession, printer_id: uuid.UUID
) -> None:
    printer = await get_printer_by_id(db, printer_id)
    await db.delete(printer)
    await db.commit()
