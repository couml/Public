from datetime import datetime
from uuid import UUID
from app.schemas.common import ORMModel
from pydantic import BaseModel, Field


class PrinterOut(ORMModel):
    """打印机完整信息响应"""

    id: str = Field(description="打印机ID")
    name: str = Field(description="打印机名称")
    brand: str = Field(description="品牌")
    model: str = Field(description="型号")
    serial_number: str | None = Field(default=None, description="序列号")
    location: str | None = Field(default=None, description="位置")
    department: str | None = Field(default=None, description="所属部门")
    ip_address: str | None = Field(default=None, description="IP地址")
    mac_address: str | None = Field(default=None, description="MAC地址")
    status: str = Field(description="状态: online/offline/error/maintenance/busy")
    is_active: bool = Field(description="是否启用")
    supported_formats: str | None = Field(default=None, description="支持的文件格式")
    resolution: str | None = Field(default=None, description="分辨率")
    color_support: bool = Field(default=False, description="是否支持彩色")
    duplex_support: bool = Field(default=False, description="是否支持双面打印")
    created_at: str = Field(description="创建时间（ISO格式）")
    updated_at: str = Field(description="更新时间（ISO格式）")

    model_config = {"from_attributes": True}


class PrinterStatusOut(ORMModel):
    """打印机实时状态响应"""

    id: str = Field(description="状态记录ID")
    printer_id: str = Field(description="打印机ID")
    status: str = Field(description="状态")
    toner_level: int | None = Field(default=None, description="碳粉剩余百分比")
    paper_level: int | None = Field(default=None, description="纸张剩余百分比")
    error_code: str | None = Field(default=None, description="错误码")
    error_message: str | None = Field(default=None, description="错误描述")
    response_time_ms: int | None = Field(default=None, description="响应时间（毫秒）")
    recorded_at: str = Field(description="记录时间（ISO格式）")

    model_config = {"from_attributes": True}


class PrinterAlertOut(ORMModel):
    """打印机告警响应"""

    id: str = Field(description="告警ID")
    printer_id: str = Field(description="打印机ID")
    alert_type: str = Field(description="告警类型")
    severity: str = Field(description="严重级别: info/warning/critical")
    message: str = Field(description="告警消息")
    is_resolved: bool = Field(default=False, description="是否已解决")
    resolved_by: str | None = Field(default=None, description="解决人ID")
    resolved_at: str | None = Field(default=None, description="解决时间（ISO格式）")
    created_at: str = Field(description="创建时间（ISO格式）")

    model_config = {"from_attributes": True}


class PrinterStatsOut(ORMModel):
    """打印机统计信息响应"""

    total_pages: int = Field(default=0, description="总打印页数")
    pages_today: int = Field(default=0, description="今日打印页数")
    pages_this_week: int = Field(default=0, description="本周打印页数")
    pages_this_month: int = Field(default=0, description="本月打印页数")
    total_errors: int = Field(default=0, description="总错误次数")
    uptime_percentage: float = Field(default=100.0, description="在线率百分比")


class PrinterListQuery(ORMModel):
    """打印机列表查询参数"""

    brand: str | None = Field(default=None, description="品牌筛选")
    status: str | None = Field(default=None, description="状态筛选")
    search: str | None = Field(default=None, description="关键词搜索")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")
