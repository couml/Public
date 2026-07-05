from __future__ import annotations
import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Uuid,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    printer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("printers.id"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("file_records.id"), nullable=False
    )
    job_name: Mapped[str | None] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(
        String(20), default="queued", server_default="queued"
    )
    copies: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    color_mode: Mapped[str] = mapped_column(
        String(16), default="grayscale", server_default="grayscale"
    )
    duplex: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    paper_size: Mapped[str] = mapped_column(
        String(10), default="A4", server_default="A4"
    )
    page_range: Mapped[str | None] = mapped_column(String(32))
    n_up: Mapped[str] = mapped_column(String(10), default="1", server_default="1")
    orientation: Mapped[str] = mapped_column(
        String(12), default="portrait", server_default="portrait"
    )
    pin_code: Mapped[str | None] = mapped_column(String(16))
    total_pages: Mapped[int | None] = mapped_column(Integer)
    pages_printed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User")
    printer: Mapped["Printer"] = relationship("Printer", back_populates="print_jobs")
    file: Mapped["FileRecord"] = relationship("FileRecord")

    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'queued', 'converting', 'waiting', 'printing', "
            "'completed', 'failed', 'cancelled'"
            ")",
            name="ck_print_jobs_status",
        ),
        CheckConstraint(
            "copies >= 1 AND copies <= 999",
            name="ck_print_jobs_copies",
        ),
        CheckConstraint(
            "color_mode IN ('color', 'grayscale')",
            name="ck_print_jobs_color_mode",
        ),
        CheckConstraint(
            "orientation IN ('portrait', 'landscape')",
            name="ck_print_jobs_orientation",
        ),
    )

    def __repr__(self) -> str:
        return f"<PrintJob {self.job_name or self.id}>"
