from __future__ import annotations

from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class DocumentOut(ORMModel):
    """扫描文档响应"""

    id: UUID = Field(description="文档ID")
    user_id: Optional[UUID] = Field(default=None, description="上传用户ID")
    printer_id: Optional[UUID] = Field(default=None, description="关联打印机ID")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小（字节）")
    mime_type: Optional[str] = Field(default=None, description="MIME类型")
    storage_path: str = Field(description="存储路径")
    page_count: Optional[int] = Field(default=None, description="页数")
    tags: list[str] = Field(default_factory=list, description="标签")
    category: Optional[str] = Field(default=None, description="分类")
    is_shared: bool = Field(default=False, description="是否已分享")
    share_token: Optional[str] = Field(default=None, description="分享令牌")
    share_expires_at: Optional[datetime] = Field(default=None, description="分享过期时间")
    created_at: datetime = Field(description="创建时间")


class ShareRequest(ORMModel):
    """文档分享请求"""

    expires_hours: int = Field(default=24, ge=1, le=8760, description="有效小时数，最大1年")


class ShareResponse(ORMModel):
    """文档分享响应"""

    share_url: str = Field(description="分享链接")
    share_token: str = Field(description="分享令牌")
    expires_at: str = Field(description="过期时间（ISO格式）")


class TagUpdate(ORMModel):
    """文档标签更新请求"""

    tags: list[str] = Field(default_factory=list, description="标签列表")
    category: Optional[str] = Field(default=None, description="分类")
