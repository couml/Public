from __future__ import annotations

from typing import Optional
from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class DriverPackageOut(ORMModel):
    """驱动包响应"""

    id: UUID = Field(description="驱动包ID")
    brand: str = Field(description="适用品牌")
    model: str = Field(description="适用型号")
    os_platform: str = Field(description="操作系统: windows/macos/linux")
    version: str = Field(description="驱动版本号")
    file_size: int = Field(description="文件大小（字节）")
    storage_path: str = Field(description="存储路径")
    download_count: int = Field(default=0, description="下载次数")
    release_date: date = Field(description="发布日期")
    changelog: Optional[str] = Field(default=None, description="更新日志")
    is_active: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class DriverListQuery(ORMModel):
    """驱动列表查询参数"""

    brand: Optional[str] = Field(default=None, description="品牌筛选")
    model: Optional[str] = Field(default=None, description="型号筛选")
    os: Optional[str] = Field(default=None, description="操作系统筛选")
    search: Optional[str] = Field(default=None, description="关键词搜索")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class HP136aPageOut(ORMModel):
    """HP 136a 专属页面响应"""

    drivers: list[DriverPackageOut] = Field(default_factory=list, description="驱动下载列表")
    manuals: list[dict] = Field(default_factory=list, description="使用手册列表")
    faqs: list[dict] = Field(default_factory=list, description="常见问题列表")
    install_guides: dict = Field(default_factory=dict, description="安装指南分类")


class DriverAdminCreate(ORMModel):
    """管理员创建驱动请求"""

    brand: str = Field(description="适用品牌")
    model: str = Field(description="适用型号")
    os_platform: str = Field(description="操作系统")
    version: str = Field(description="驱动版本号")
    file_size: int = Field(description="文件大小（字节）")
    storage_path: str = Field(description="存储路径")
    release_date: str = Field(description="发布日期（ISO格式）")
    changelog: Optional[str] = Field(default=None, description="更新日志")
