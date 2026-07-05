from __future__ import annotations

from typing import Optional
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
    serial_number: Optional[str] = None
    ip_address: str
    mac_address: Optional[str] = None
    location: Optional[str] = None
    status: str
    toner_level: int = 0
    toner_type: Optional[str] = None
    paper_level: int = 0
    total_pages_printed: int = 0
    firmware_version: Optional[str] = None
    snmp_community: str = "public"
    snmp_port: int = 161
    supports_color: bool = False
    supports_duplex: bool = False
    max_paper_size: str = "A4"
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PrinterStatusOut(ORMModel):
    """打印机实时状态响应"""

    id: UUID
    printer_id: UUID
    status: str
    toner_level: Optional[int] = None
    paper_level: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    response_time_ms: Optional[int] = None
    recorded_at: datetime


class PrinterAlertOut(ORMModel):
    """打印机告警响应"""

    id: UUID
    printer_id: UUID
    alert_type: str
    severity: str
    message: str
    is_resolved: bool = False
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
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

    brand: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
