from __future__ import annotations
import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Uuid,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScanDocument(Base):
    __tablename__ = "scan_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    printer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("printers.id"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[int] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    storage_path: Mapped[str] = mapped_column(String(1024))
    page_count: Mapped[int | None] = mapped_column(Integer)
    ocr_text: Mapped[str | None] = mapped_column(Text)
    ocr_status: Mapped[str] = mapped_column(
        String(16), default="pending", server_default="pending"
    )
    tags: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    category: Mapped[str | None] = mapped_column(String(64))
    is_shared: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    share_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "ocr_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_scan_documents_ocr_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<ScanDocument {self.filename}>"
