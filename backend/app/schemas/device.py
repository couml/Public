from __future__ import annotations
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class PrinterOut(ORMModel):
    """打印机完整信息响应"""

    id: UUID
    name: str
    brand: str
    model: str
    serial_number: str | None = None
    ip_address: str
    mac_address: str | None = None
    location: str | None = None
    status: str
    toner_level: int = 0
    toner_type: str | None = None
    paper_level: int = 0
    total_pages_printed: int = 0
    firmware_version: str | None = None
    snmp_community: str = "public"
    snmp_port: int = 161
    supports_color: bool = False
    supports_duplex: bool = False
    max_paper_size: str = "A4"
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PrinterStatusOut(ORMModel):
    """打印机实时状态响应"""

    id: UUID
    printer_id: UUID
    status: str
    toner_level: int | None = None
    paper_level: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    ip_address: str | None = None
    response_time_ms: int | None = None
    recorded_at: datetime


class PrinterAlertOut(ORMModel):
    """打印机告警响应"""

    id: UUID
    printer_id: UUID
    alert_type: str
    severity: str
    message: str
    is_resolved: bool = False
    resolved_by: UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class PrinterStatsOut(ORMModel):
    """打印机统计信息响应"""

    total_pages: int = 0
    pages_today: int = 0
    pages_this_week: int = 0
    pages_this_month: int = 0
    total_errors: int = 0
    uptime_percentage: float = 100.0


class PrinterListQuery(ORMModel):
    """打印机列表查询参数"""

    brand: str | None = None
    status: str | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
