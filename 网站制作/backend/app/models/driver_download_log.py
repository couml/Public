import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Uuid, DateTime, ForeignKey, String, Text, func

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DriverDownloadLog(Base):
    __tablename__ = "driver_download_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("driver_packages.id"), nullable=False
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<DriverDownloadLog {self.id}>"
