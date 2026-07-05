from __future__ import annotations

from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class SessionCreate(ORMModel):
    """创建诊断会话请求"""

    printer_id: Optional[UUID] = Field(default=None, description="关联打印机ID")
    title: Optional[str] = Field(default=None, description="会话标题")


class MessageCreate(ORMModel):
    """发送诊断消息请求"""

    message: str = Field(description="用户消息内容")


class DiagnosisResultSchema(ORMModel):
    """AI诊断结果"""

    fault_type: str = Field(description="故障类型")
    root_cause: str = Field(description="根本原因")
    severity: str = Field(description="严重级别: low/medium/high/critical")
    steps: list[str] = Field(default_factory=list, description="修复步骤")
    parts: list[str] = Field(default_factory=list, description="所需零件")
    safety: list[str] = Field(default_factory=list, description="安全注意事项")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")


class MessageOut(ORMModel):
    """诊断消息响应"""

    id: UUID = Field(description="消息ID")
    session_id: UUID = Field(description="会话ID")
    role: str = Field(description="角色: user/assistant/system")
    message: str = Field(description="消息内容")
    diagnosis_result: DiagnosisResultSchema | None = Field(default=None, description="诊断结果（仅assistant消息）")
    step_number: Optional[int] = Field(default=None, description="步骤序号")
    created_at: datetime = Field(description="创建时间")


class SessionOut(ORMModel):
    """诊断会话响应"""

    id: UUID = Field(description="会话ID")
    user_id: UUID = Field(description="用户ID")
    printer_id: Optional[UUID] = Field(default=None, description="关联打印机ID")
    session_title: Optional[str] = Field(default=None, description="会话标题")
    status: str = Field(description="状态: active/completed/archived")
    error_codes: list[str] = Field(default_factory=list, description="相关错误码")
    resolution_summary: Optional[str] = Field(default=None, description="解决方案摘要")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    messages: list[MessageOut] | None = Field(default=None, description="消息列表")


class PredictRequest(ORMModel):
    """故障预测请求"""

    printer_id: str = Field(description="打印机ID")
