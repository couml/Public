from datetime import datetime
from uuid import UUID
from app.schemas.common import ORMModel
from pydantic import BaseModel, Field


class UploadInitRequest(ORMModel):
    """分片上传初始化请求"""

    filename: str = Field(description="原始文件名")
    file_size: int = Field(description="文件总大小（字节）")
    file_md5: str = Field(description="文件MD5哈希值")
    total_chunks: int = Field(description="分片总数")
    mime_type: str | None = Field(default=None, description="MIME类型")


class UploadInitResponse(ORMModel):
    """分片上传初始化响应"""

    upload_id: str = Field(description="上传会话ID")
    file_id: str = Field(description="文件记录ID")


class UploadCompleteRequest(ORMModel):
    """分片上传完成请求"""

    upload_id: str = Field(description="上传会话ID")
    file_id: str = Field(description="文件记录ID")


class FileRecordOut(ORMModel):
    """文件记录响应"""

    id: str = Field(description="文件ID")
    user_id: str = Field(description="上传用户ID")
    original_filename: str = Field(description="原始文件名")
    file_size: int = Field(description="文件大小（字节）")
    mime_type: str | None = Field(default=None, description="MIME类型")
    file_md5: str | None = Field(default=None, description="文件MD5")
    storage_path: str = Field(description="存储路径")
    status: str = Field(description="状态: uploading/ready/processing/completed/failed")
    converted_format: str | None = Field(default=None, description="转换后格式")
    converted_path: str | None = Field(default=None, description="转换后文件路径")
    page_count: int | None = Field(default=None, description="页数")
    is_temporary: bool = Field(default=False, description="是否临时文件")
    expires_at: str | None = Field(default=None, description="过期时间（ISO格式）")
    created_at: str = Field(description="创建时间（ISO格式）")

    model_config = {"from_attributes": True}


class ConvertRequest(ORMModel):
    """文件格式转换请求"""

    file_id: str = Field(description="文件ID")
    target_format: str = Field(description="目标格式（如pdf、png）")


class StagingFileOut(ORMModel):
    """暂存文件响应（简化版）"""

    id: str = Field(description="文件ID")
    user_id: str = Field(description="上传用户ID")
    original_filename: str = Field(description="原始文件名")
    file_size: int = Field(description="文件大小")
    mime_type: str | None = Field(default=None, description="MIME类型")
    status: str = Field(description="状态")
    is_temporary: bool = Field(default=False, description="是否临时文件")
    expires_at: str | None = Field(default=None, description="过期时间（ISO格式）")
    created_at: str = Field(description="创建时间（ISO格式）")

    model_config = {"from_attributes": True}
