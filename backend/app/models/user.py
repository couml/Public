from __future__ import annotations
import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Uuid, Boolean, CheckConstraint, DateTime, String, func

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=lambda: uuid4(),
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(
        String(20), default="user", server_default="user"
    )
    department: Mapped[str | None] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'it_staff', 'user')",
            name="ck_users_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
