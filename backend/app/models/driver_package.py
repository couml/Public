from __future__ import annotations
import uuid
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import (
    Uuid,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DriverPackage(Base):
    __tablename__ = "driver_packages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    os_platform: Mapped[str] = mapped_column(String(12))
    version: Mapped[str] = mapped_column(String(32))
    file_size: Mapped[int] = mapped_column(BigInteger)
    storage_path: Mapped[str] = mapped_column(String(1024))
    release_date: Mapped[date] = mapped_column(Date)
    changelog: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    download_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "os_platform IN ('windows', 'macos', 'linux')",
            name="ck_driver_packages_os_platform",
        ),
        UniqueConstraint(
            "brand", "model", "os_platform", "version",
            name="uq_driver_packages_brand_model_os_version",
        ),
    )

    def __repr__(self) -> str:
        return f"<DriverPackage {self.brand} {self.model} {self.version}>"
