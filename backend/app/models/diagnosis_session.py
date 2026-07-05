from typing import List
import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Uuid, CheckConstraint, DateTime, ForeignKey, JSON, String, Text, func

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DiagnosisSession(Base):
    __tablename__ = "diagnosis_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    printer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("printers.id"), nullable=True
    )
    session_title: Mapped[str] = mapped_column(
        String(256), default="New Diagnosis", server_default="New Diagnosis"
    )
    status: Mapped[str] = mapped_column(
        String(16), default="active", server_default="active"
    )
    error_codes: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    resolution_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User")
    printer: Mapped["Printer"] = relationship("Printer")
    messages: Mapped[List["DiagnosisConversation"]] = relationship(
        "DiagnosisConversation", back_populates="session"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'resolved', 'closed')",
            name="ck_diagnosis_sessions_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<DiagnosisSession {self.session_title}>"
