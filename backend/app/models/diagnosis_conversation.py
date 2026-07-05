import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Uuid, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DiagnosisConversation(Base):
    __tablename__ = "diagnosis_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("diagnosis_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    diagnosis_result: Mapped[dict | None] = mapped_column(JSON)
    sources: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    step_number: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["DiagnosisSession"] = relationship(
        "DiagnosisSession", back_populates="messages"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="ck_diagnosis_conversations_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<DiagnosisConversation {self.role}>"
