import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Uuid, DateTime, ForeignKey, Integer, String, Text, func

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PrinterStatusLog(Base):
    __tablename__ = "printer_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    printer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("printers.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20))
    toner_level: Mapped[int | None] = mapped_column(Integer)
    paper_level: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    printer: Mapped["Printer"] = relationship(
        "Printer", back_populates="status_logs"
    )

    def __repr__(self) -> str:
        return f"<PrinterStatusLog {self.id}>"
