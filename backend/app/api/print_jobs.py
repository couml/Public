from __future__ import annotations
import asyncio
import random
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.file_record import FileRecord
from app.models.printer import Printer
from app.models.print_job import PrintJob
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.print_job import PrintJobCreate, PrintJobOut, PrintJobStatsOut

router = APIRouter(prefix="/print/jobs")


async def simulate_job_progression(
    job_id: uuid.UUID,
    db_session_factory,
):
    """Background task: simulate job status progression."""
    await asyncio.sleep(5)  # Simulate initial processing

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PrintJob).where(PrintJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job or job.status == "cancelled":
            return

        # Move to printing
        job.status = "printing"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        await asyncio.sleep(8)  # Simulate printing time

        # Refresh
        await session.refresh(job)

        if job.status == "cancelled":
            return

        # Complete
        job.status = "completed"
        job.pages_printed = job.copies * random.randint(1, 20)
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()


@router.post("", response_model=PrintJobOut, status_code=status.HTTP_201_CREATED)
async def submit_print_job(
    body: PrintJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new print job."""
    # Validate printer exists and is online
    try:
        printer_id = uuid.UUID(body.printer_id)
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

    if printer.status not in ("online", "busy"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Printer is not available",
        )

    # Validate file exists and is converted (if not original format)
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

    if file_record.status not in ("uploaded", "converted"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not ready for printing",
        )

    # Create print job
    job = PrintJob(
        user_id=current_user.id,
        printer_id=printer_id,
        file_id=file_id,
        job_name=file_record.original_filename,
        status="queued",
        copies=body.copies,
        color_mode=body.color_mode,
        duplex=body.duplex,
        paper_size=body.paper_size,
        page_range=body.page_range,
        n_up=body.n_up,
        orientation=body.orientation,
        pin_code=body.pin_code,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Start background simulation
    background_tasks.add_task(simulate_job_progression, job.id, None)

    return job


@router.get("", response_model=PaginatedResponse[PrintJobOut])
async def list_print_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's print jobs."""
    query = select(PrintJob).where(PrintJob.user_id == current_user.id)

    if status_filter:
        query = query.where(PrintJob.status == status_filter)

    query = query.order_by(PrintJob.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return PaginatedResponse(
        items=jobs,
        total=len(jobs),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.get("/{id}", response_model=PrintJobOut)
async def get_print_job(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get print job detail."""
    try:
        job_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        )

    result = await db.execute(
        select(PrintJob).where(
            PrintJob.id == job_id,
            PrintJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Print job not found",
        )

    return job


@router.post("/{id}/cancel")
async def cancel_print_job(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a print job (only if queued or waiting)."""
    try:
        job_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        )

    result = await db.execute(
        select(PrintJob).where(
            PrintJob.id == job_id,
            PrintJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Print job not found",
        )

    if job.status not in ("queued", "waiting"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status '{job.status}'",
        )

    job.status = "cancelled"
    await db.commit()

    return {"success": True, "message": "Job cancelled"}


@router.get("/stats", response_model=PrintJobStatsOut)
async def get_print_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get print statistics for current user (mock data)."""
    return PrintJobStatsOut(
        total_jobs=random.randint(10, 200),
        completed_today=random.randint(0, 20),
        failed_today=random.randint(0, 3),
        total_pages_today=random.randint(0, 500),
        avg_wait_seconds=round(random.uniform(5.0, 120.0), 1),
    )
