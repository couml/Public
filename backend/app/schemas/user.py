from __future__ import annotations
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class UserOut(ORMModel):
    """用户信息响应"""

    id: UUID
    username: str
    email: str
    full_name: str | None = None
    role: str
    department: str | None = None
    is_active: bool
    created_at: datetime


class UserUpdate(ORMModel):
    """用户信息更新请求"""

    full_name: str | None = Field(default=None, description="全名")
    department: str | None = Field(default=None, description="部门")
    role: str | None = Field(default=None, description="角色")
    is_active: bool | None = Field(default=None, description="是否激活")
