from datetime import date, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, model_serializer


T = TypeVar("T")


class ORMModel(BaseModel):
    """Base model that converts all UUID/datetime/date to JSON-safe types."""

    model_config = {"from_attributes": True}

    @model_serializer(mode="wrap")
    def _serialize(self, handler, info):
        """Walk the serialized result and convert UUID/datetime/date to strings."""
        result = handler(self)
        _convert_to_json_safe(result)
        return result


def _convert_to_json_safe(obj: Any) -> Any:
    """Recursively convert UUID/datetime/date objects to strings."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            if isinstance(val, UUID):
                obj[key] = str(val)
            elif isinstance(val, datetime):
                obj[key] = val.isoformat()
            elif isinstance(val, date):
                obj[key] = val.isoformat()
            elif isinstance(val, list):
                for item in val:
                    _convert_to_json_safe(item)
            elif isinstance(val, dict):
                _convert_to_json_safe(val)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (UUID, datetime, date)):
                idx = obj.index(item)
                obj[idx] = str(item) if isinstance(item, UUID) else item.isoformat()
            elif isinstance(item, (dict, list)):
                _convert_to_json_safe(item)


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
