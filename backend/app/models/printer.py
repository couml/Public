from typing import List
import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Uuid, BigInteger, Boolean, CheckConstraint, DateTime, Integer, String, func

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Printer(Base):
    __tablename__ = "printers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    name: Mapped[str] = mapped_column(String(128))
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    serial_number: Mapped[str | None] = mapped_column(String(128), unique=True)
    ip_address: Mapped[str] = mapped_column(String(45))
    mac_address: Mapped[str | None] = mapped_column(String(17))
    location: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(20), default="offline", server_default="offline"
    )
    toner_level: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    toner_type: Mapped[str | None] = mapped_column(String(64))
    paper_level: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_pages_printed: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0"
    )
    firmware_version: Mapped[str | None] = mapped_column(String(32))
    snmp_community: Mapped[str] = mapped_column(
        String(64), default="public", server_default="public"
    )
    snmp_port: Mapped[int] = mapped_column(Integer, default=161, server_default="161")
    supports_color: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    supports_duplex: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    max_paper_size: Mapped[str] = mapped_column(
        String(10), default="A4", server_default="A4"
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    status_logs: Mapped[List["PrinterStatusLog"]] = relationship(
        "PrinterStatusLog", back_populates="printer"
    )
    alerts: Mapped[List["PrinterAlert"]] = relationship(
        "PrinterAlert", back_populates="printer"
    )
    print_jobs: Mapped[List["PrintJob"]] = relationship(
        "PrintJob", back_populates="printer"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('online', 'offline', 'busy', 'error')",
            name="ck_printers_status",
        ),
        CheckConstraint(
            "toner_level >= 0 AND toner_level <= 100",
            name="ck_printers_toner_level",
        ),
        CheckConstraint(
            "paper_level >= 0 AND paper_level <= 100",
            name="ck_printers_paper_level",
        ),
    )

    def __repr__(self) -> str:
        return f"<Printer {self.name}>"
