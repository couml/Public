from __future__ import annotations

from typing import Optional
import asyncio
import random
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FileRecord, PrintJob, Printer


async def _simulate_job_progression(db_factory, job_id: uuid.UUID):
    """Background task: simulate print job lifecycle."""
    await asyncio.sleep(5)

    async with db_factory() as db:
        result = await db.execute(
            select(PrintJob).where(PrintJob.id == job_id)
        )
        job = result.scalars().first()
        if not job or job.status == "cancelled":
            return

        job.status = "printing"
        job.started_at = datetime.now(timezone.utc)
        await db.commit()

    # Simulate printing duration
    print_duration = random.uniform(5, 15)
    await asyncio.sleep(print_duration)

    async with db_factory() as db:
        result = await db.execute(
            select(PrintJob).where(PrintJob.id == job_id)
        )
        job = result.scalars().first()
        if not job or job.status == "cancelled":
            return

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.total_pages = random.randint(1, 50)
        job.pages_printed = job.total_pages
        await db.commit()


async def submit_job(
    db: AsyncSession,
    user_id: uuid.UUID,
    job_data: dict,
) -> PrintJob:
    printer_id = job_data.get("printer_id")
    file_id = job_data.get("file_id")

    # Validate printer
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalars().first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    if printer.status == "offline":
        raise HTTPException(
            status_code=400, detail="Printer is offline"
        )

    # Validate file
    result = await db.execute(
        select(FileRecord).where(FileRecord.id == file_id)
    )
    file_record = result.scalars().first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if file_record.status not in ("uploaded", "converted"):
        raise HTTPException(
            status_code=400,
            detail=f"File status is '{file_record.status}', must be uploaded or converted",
        )

    job = PrintJob(
        user_id=user_id,
        printer_id=printer_id,
        file_id=file_id,
        job_name=job_data.get("job_name", file_record.original_filename),
        status="queued",
        copies=job_data.get("copies", 1),
        color_mode=job_data.get("color_mode", "grayscale"),
        duplex=job_data.get("duplex", False),
        paper_size=job_data.get("paper_size", "A4"),
        page_range=job_data.get("page_range"),
        n_up=job_data.get("n_up", "1"),
        orientation=job_data.get("orientation", "portrait"),
        pin_code=job_data.get("pin_code"),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Start background simulation — note: caller must provide db_factory
    # We store the session factory reference for the caller to use
    return job


async def get_user_jobs(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[PrintJob], int]:
    conditions = [PrintJob.user_id == user_id]
    if status:
        conditions.append(PrintJob.status == status)

    base_query = select(PrintJob).where(and_(*conditions))

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        base_query
        .order_by(PrintJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    jobs = list(result.scalars().all())

    return jobs, total


async def get_job_by_id(db: AsyncSession, job_id: uuid.UUID) -> PrintJob:
    result = await db.execute(select(PrintJob).where(PrintJob.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")
    return job


async def cancel_job(
    db: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID
) -> PrintJob:
    result = await db.execute(select(PrintJob).where(PrintJob.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")

    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your job")

    if job.status not in ("queued", "waiting"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status '{job.status}'",
        )

    job.status = "cancelled"
    job.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)
    return job


async def get_user_stats(
    db: AsyncSession, user_id: uuid.UUID
) -> dict:
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Total jobs
    total_result = await db.execute(
        select(func.count()).where(PrintJob.user_id == user_id)
    )
    total_jobs = total_result.scalar_one()

    # Completed today
    completed_today_result = await db.execute(
        select(func.count()).where(
            and_(
                PrintJob.user_id == user_id,
                PrintJob.status == "completed",
                PrintJob.completed_at >= today_start,
            )
        )
    )
    completed_today = completed_today_result.scalar_one()

    # Failed today
    failed_today_result = await db.execute(
        select(func.count()).where(
            and_(
                PrintJob.user_id == user_id,
                PrintJob.status == "failed",
                PrintJob.completed_at >= today_start,
            )
        )
    )
    failed_today = failed_today_result.scalar_one()

    # Total pages today
    pages_result = await db.execute(
        select(func.coalesce(func.sum(PrintJob.total_pages), 0)).where(
            and_(
                PrintJob.user_id == user_id,
                PrintJob.status == "completed",
                PrintJob.completed_at >= today_start,
            )
        )
    )
    total_pages_today = pages_result.scalar_one()

    return {
        "total_jobs": total_jobs,
        "completed_today": completed_today,
        "failed_today": failed_today,
        "total_pages_today": total_pages_today,
        "avg_wait_seconds": round(random.uniform(3.0, 30.0), 1),
    }
