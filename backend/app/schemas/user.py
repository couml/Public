from __future__ import annotations

from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class UserOut(ORMModel):
    """用户信息响应"""

    id: UUID
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    department: Optional[str] = None
    is_active: bool
    created_at: datetime


class UserUpdate(ORMModel):
    """用户信息更新请求"""

    full_name: Optional[str] = Field(default=None, description="全名")
    department: Optional[str] = Field(default=None, description="部门")
    role: Optional[str] = Field(default=None, description="角色")
    is_active: Optional[bool] = Field(default=None, description="是否激活")
