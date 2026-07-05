import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Printer, PrinterAlert

logger = logging.getLogger("printer_management.alerts")


async def create_alert(
    db: AsyncSession,
    printer_id: uuid.UUID,
    alert_type: str,
    severity: str,
    message: str,
) -> PrinterAlert:
    alert = PrinterAlert(
        printer_id=printer_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        is_resolved=False,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


async def check_and_notify(
    db: AsyncSession,
    alert: PrinterAlert,
) -> None:
    """
    Placeholder for email/webhook notification dispatch.
    In production: send email to IT staff, push to webhook, etc.
    """
    from sqlalchemy import select

    result = await db.execute(
        select(Printer).where(Printer.id == alert.printer_id)
    )
    printer = result.scalars().first()
    printer_name = printer.name if printer else "Unknown"

    logger.info(
        "Alert created [%s] for printer %s (%s): %s",
        alert.severity.upper(),
        printer_name,
        alert.alert_type,
        alert.message,
    )

    # Future integration points:
    # - await send_email(admin_email, subject, body)
    # - await send_webhook(webhook_url, payload)
    # - await send_slack_notification(channel, message)
    # - await send_wechat_work(webhook, alert)
