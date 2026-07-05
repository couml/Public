from __future__ import annotations
import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Uuid, BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, func

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FileRecord(Base):
    __tablename__ = "file_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(512))
    stored_filename: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[int] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    file_md5: Mapped[str] = mapped_column(String(64))
    storage_path: Mapped[str] = mapped_column(String(1024))
    chunk_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    status: Mapped[str] = mapped_column(
        String(20), default="uploaded", server_default="uploaded"
    )
    converted_format: Mapped[str | None] = mapped_column(String(16))
    converted_path: Mapped[str | None] = mapped_column(String(1024))
    page_count: Mapped[int | None] = mapped_column(Integer)
    is_temporary: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    owner: Mapped["User"] = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "status IN ('uploading', 'uploaded', 'converting', 'converted', 'failed')",
            name="ck_file_records_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<FileRecord {self.original_filename}>"
