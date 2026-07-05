from __future__ import annotations
import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Uuid, Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, func

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PrinterAlert(Base):
    __tablename__ = "printer_alerts"

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
    alert_type: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(
        String(12), default="warning", server_default="warning"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    printer: Mapped["Printer"] = relationship("Printer", back_populates="alerts")
    resolver: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ("
            "'paper_out', 'paper_jam', 'paper_low', "
            "'toner_low', 'toner_empty', 'offline', "
            "'service_required', 'fuser_warning', 'drum_low'"
            ")",
            name="ck_printer_alerts_alert_type",
        ),
        CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name="ck_printer_alerts_severity",
        ),
    )

    def __repr__(self) -> str:
        return f"<PrinterAlert {self.alert_type}>"
