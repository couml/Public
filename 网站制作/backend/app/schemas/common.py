from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


T = TypeVar("T")


class ORMModel(BaseModel):
    """Base model that handles UUID and datetime serialization from ORM objects."""

    model_config = {"from_attributes": True}

    @field_serializer("id", check_fields=False)
    def serialize_id(self, value: UUID) -> str:
        return str(value)

    @field_serializer("created_at", check_fields=False)
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("updated_at", check_fields=False)
    def serialize_updated_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("recorded_at", check_fields=False)
    def serialize_recorded_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("queued_at", check_fields=False)
    def serialize_queued_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("started_at", check_fields=False)
    def serialize_started_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("completed_at", check_fields=False)
    def serialize_completed_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("last_seen_at", check_fields=False)
    def serialize_last_seen_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("expires_at", check_fields=False)
    def serialize_expires_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("share_expires_at", check_fields=False)
    def serialize_share_expires_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("resolved_at", check_fields=False)
    def serialize_resolved_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("downloaded_at", check_fields=False)
    def serialize_downloaded_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("release_date", check_fields=False)
    def serialize_release_date(self, value: datetime) -> str:
        return value.isoformat()


class PaginationParams(BaseModel):
    """通用分页请求参数"""

    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")


class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应"""

    items: list[T] = Field(default_factory=list, description="当前页数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条数")
    total_pages: int = Field(description="总页数")

    model_config = {"from_attributes": True}


class BaseResponse(BaseModel):
    """基础成功响应"""

    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="OK", description="响应消息")


class ErrorResponse(BaseModel):
    """基础错误响应"""

    success: bool = Field(default=False, description="是否成功")
    message: str = Field(description="错误消息")
    error_code: str | None = Field(default=None, description="错误码")
