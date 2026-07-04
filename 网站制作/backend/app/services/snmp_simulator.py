import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Printer, PrinterAlert, PrinterStatusLog
from app.services.alert_service import check_and_notify, create_alert

logger = logging.getLogger("printer_management.snmp_simulator")

# ---------------------------------------------------------------------------
# Fault scenario definitions (8+ scenarios)
# ---------------------------------------------------------------------------
FAULT_SCENARIOS: list[dict] = [
    {
        "error_code": "13.01",
        "alert_type": "paper_jam",
        "message": "[模拟] 进纸区域检测到卡纸",
        "probability": 0.15,
    },
    {
        "error_code": "13.20",
        "alert_type": "paper_jam",
        "message": "[模拟] 定影区域检测到卡纸",
        "probability": 0.10,
    },
    {
        "error_code": "50.2",
        "alert_type": "fuser_warning",
        "message": "[模拟] 定影单元温度异常，加热器可能故障",
        "probability": 0.08,
    },
    {
        "error_code": "10.0001",
        "alert_type": "toner_low",
        "message": "[模拟] 碳粉余量低于 5%，请准备新硒鼓",
        "probability": 0.20,
    },
    {
        "error_code": "11.01",
        "alert_type": "paper_out",
        "message": "[模拟] 进纸失败，取纸轮可能磨损",
        "probability": 0.10,
    },
    {
        "error_code": "49.FF",
        "alert_type": "service_required",
        "message": "[模拟] 固件异常重启，需要升级固件",
        "probability": 0.05,
    },
    {
        "error_code": "30.03",
        "alert_type": "service_required",
        "message": "[模拟] 扫描仪校准失败",
        "probability": 0.07,
    },
    {
        "error_code": "54.01",
        "alert_type": "service_required",
        "message": "[模拟] 转印辊高压异常",
        "probability": 0.08,
    },
    {
        "error_code": "59.C0",
        "alert_type": "service_required",
        "message": "[模拟] 主驱动电机启动异常",
        "probability": 0.05,
    },
    {
        "error_code": "20.00",
        "alert_type": "paper_jam",
        "message": "[模拟] 前舱门未正确关闭",
        "probability": 0.12,
    },
]

STATUS_WEIGHTS = {
    "online": 0.75,
    "busy": 0.10,
    "error": 0.05,
    "offline": 0.10,
}


def _weighted_status() -> str:
    choices, weights = zip(*STATUS_WEIGHTS.items())
    return random.choices(choices, weights=weights, k=1)[0]


async def simulate_device_polling(
    db_session_factory,
    redis_client,
):
    """
    Infinite background loop that simulates SNMP device polling.
    Runs every 3 seconds, updating printer status and publishing to Redis.
    """
    logger.info("SNMP simulator started")

    while True:
        try:
            async with db_session_factory() as db:
                result = await db.execute(
                    select(Printer).where(Printer.status != "offline")
                )
                printers = list(result.scalars().all())

                for printer in printers:
                    try:
                        # -- Toner level: slowly decrease -------------------
                        new_toner = max(0, printer.toner_level - 0.01)
                        printer.toner_level = round(new_toner, 2)

                        # -- Paper level: random variation ------------------
                        delta = random.randint(-5, 5)
                        new_paper = max(0, min(100, printer.paper_level + delta))
                        printer.paper_level = new_paper

                        now = datetime.now(timezone.utc)
                        printer.last_seen_at = now

                        # -- Random fault injection (0.1% per printer/cycle) --
                        new_status = _weighted_status()
                        error_code = None
                        error_message = None

                        if random.random() < 0.001:
                            scenario = random.choice(FAULT_SCENARIOS)
                            new_status = "error"
                            error_code = scenario["error_code"]
                            error_message = scenario["message"]

                            await create_alert(
                                db,
                                printer_id=printer.id,
                                alert_type=scenario["alert_type"],
                                severity="warning" if scenario["alert_type"] == "paper_jam"
                                else "critical" if "50." in (scenario.get("error_code") or "")
                                else "info",
                                message=scenario["message"],
                            )

                        # Auto-resolve if no current error
                        if (
                            new_status != "error"
                            and printer.status == "error"
                        ):
                            new_status = "online"

                        printer.status = new_status

                        # -- Create status log --------------------------------
                        log_entry = PrinterStatusLog(
                            printer_id=printer.id,
                            status=new_status,
                            toner_level=round(new_toner),
                            paper_level=new_paper,
                            error_code=error_code,
                            error_message=error_message,
                            ip_address=printer.ip_address,
                            response_time_ms=random.randint(5, 200),
                        )
                        db.add(log_entry)

                        # -- Publish to Redis ---------------------------------
                        status_payload = {
                            "printer_id": str(printer.id),
                            "name": printer.name,
                            "status": new_status,
                            "toner_level": round(new_toner, 2),
                            "paper_level": new_paper,
                            "error_code": error_code,
                            "error_message": error_message,
                            "last_seen_at": now.isoformat(),
                            "timestamp": now.isoformat(),
                        }

                        try:
                            await redis_client.publish(
                                f"device:{printer.id}:status",
                                json.dumps(status_payload),
                            )
                            await redis_client.setex(
                                f"device:{printer.id}:status:latest",
                                300,  # 5 minute TTL
                                json.dumps(status_payload),
                            )
                        except Exception as redis_err:
                            logger.warning(
                                "Redis publish failed for printer %s: %s",
                                printer.id,
                                redis_err,
                            )

                    except Exception as inner_exc:
                        logger.error(
                            "Error polling printer %s: %s",
                            printer.id,
                            inner_exc,
                        )

                await db.commit()

        except Exception as exc:
            logger.error("SNMP simulator cycle error: %s", exc)

        await asyncio.sleep(3)
