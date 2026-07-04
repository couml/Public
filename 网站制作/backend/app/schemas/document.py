from datetime import datetime
from uuid import UUID
from app.schemas.common import ORMModel
from pydantic import BaseModel, Field


class DocumentOut(ORMModel):
    """扫描文档响应"""

    id: str = Field(description="文档ID")
    user_id: str = Field(description="上传用户ID")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小（字节）")
    mime_type: str | None = Field(default=None, description="MIME类型")
    storage_path: str = Field(description="存储路径")
    page_count: int | None = Field(default=None, description="页数")
    tags: list[str] = Field(default_factory=list, description="标签")
    category: str | None = Field(default=None, description="分类")
    is_shared: bool = Field(default=False, description="是否已分享")
    share_token: str | None = Field(default=None, description="分享令牌")
    share_expires_at: str | None = Field(default=None, description="分享过期时间（ISO格式）")
    created_at: str = Field(description="创建时间（ISO格式）")

    model_config = {"from_attributes": True}


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
    category: str | None = Field(default=None, description="分类")
