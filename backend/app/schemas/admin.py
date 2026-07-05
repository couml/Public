from __future__ import annotations
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class AdminLogOut(ORMModel):
    """管理操作日志响应"""

    id: UUID = Field(description="日志ID")
    user_id: UUID | None = Field(default=None, description="操作用户ID")
    action: str = Field(description="操作类型")
    resource: str = Field(description="资源类型")
    resource_id: str | None = Field(default=None, description="资源ID")
    detail: dict | None = Field(default=None, description="操作详情")
    ip_address: str | None = Field(default=None, description="操作IP地址")
    created_at: datetime = Field(description="操作时间")


class AdminStatsOut(ORMModel):
    """管理后台统计响应"""

    total_users: int = Field(default=0, description="总用户数")
    total_printers: int = Field(default=0, description="总打印机数")
    total_jobs_today: int = Field(default=0, description="今日打印任务数")
    total_storage_bytes: int = Field(default=0, description="总存储占用（字节）")
    active_alerts: int = Field(default=0, description="活跃告警数")
    recent_logs: list[AdminLogOut] = Field(default_factory=list, description="最近操作日志")
