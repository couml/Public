from __future__ import annotations
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class PrintJobCreate(ORMModel):
    """创建打印任务请求"""

    printer_id: str = Field(description="目标打印机ID")
    file_id: str = Field(description="打印文件ID")
    copies: int = Field(default=1, ge=1, le=999, description="打印份数")
    color_mode: str = Field(default="grayscale", description="色彩模式: grayscale/color")
    duplex: bool = Field(default=False, description="是否双面打印")
    paper_size: str = Field(default="A4", description="纸张尺寸")
    page_range: str | None = Field(default=None, description="页码范围（如1-5）")
    n_up: str = Field(default="1", description="每页打印版面数: 1/2/4/6/9/16")
    orientation: str = Field(default="portrait", description="纸张方向: portrait/landscape")
    pin_code: str | None = Field(default=None, description="安全打印PIN码")


class PrintJobOut(ORMModel):
    """打印任务响应"""

    id: UUID = Field(description="任务ID")
    user_id: UUID = Field(description="用户ID")
    printer_id: UUID = Field(description="打印机ID")
    file_id: UUID = Field(description="文件ID")
    status: str = Field(description="状态: pending/processing/completed/failed/cancelled")
    copies: int = Field(description="打印份数")
    color_mode: str = Field(description="色彩模式")
    duplex: bool = Field(description="是否双面")
    paper_size: str = Field(description="纸张尺寸")
    page_range: str | None = Field(default=None, description="页码范围")
    n_up: str = Field(description="每页版面数")
    orientation: str = Field(description="纸张方向")
    total_pages: int | None = Field(default=None, description="总页数")
    pages_printed: int = Field(default=0, description="已打印页数")
    error_message: str | None = Field(default=None, description="错误信息")
    pin_code: str | None = Field(default=None, description="安全打印PIN码")
    queued_at: datetime = Field(description="排队时间")
    started_at: datetime | None = Field(default=None, description="开始时间")
    completed_at: datetime | None = Field(default=None, description="完成时间")
    created_at: datetime = Field(description="创建时间")


class PrintJobStatsOut(ORMModel):
    """打印任务统计响应"""

    total_jobs: int = Field(default=0, description="总任务数")
    completed_today: int = Field(default=0, description="今日已完成数")
    failed_today: int = Field(default=0, description="今日失败数")
    total_pages_today: int = Field(default=0, description="今日总页数")
    avg_wait_seconds: float = Field(default=0.0, description="平均等待时间（秒）")
