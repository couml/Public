"""Seed the database with initial data: admin user, printers, drivers, sample documents."""

import asyncio
import sys
import os
from datetime import date, datetime, timedelta
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.models.user import User
from app.models.printer import Printer
from app.models.printer_status_log import PrinterStatusLog
from app.models.printer_alert import PrinterAlert
from app.models.driver_package import DriverPackage
from app.models.scan_document import ScanDocument
from app.models.print_job import PrintJob
from app.models.file_record import FileRecord
from app.core.security import hash_password


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # === Users ===
        admin = User(
            username="admin",
            email="admin@printerplatform.com",
            hashed_password=hash_password("admin123"),
            full_name="系统管理员",
            role="admin",
            department="IT",
        )
        it_staff = User(
            username="itstaff",
            email="it@printerplatform.com",
            hashed_password=hash_password("it123456"),
            full_name="IT运维",
            role="it_staff",
            department="IT",
        )
        normal_user = User(
            username="zhangsan",
            email="zhangsan@example.com",
            hashed_password=hash_password("user1234"),
            full_name="张三",
            role="user",
            department="研发部",
        )
        db.add_all([admin, it_staff, normal_user])
        await db.flush()

        # === Printers (1 active HP Laser MFP 136a, rest offline) ===
        printer_data = [
            {"name": "HP Laser MFP 136a", "brand": "HP", "model": "Laser MFP 136a", "ip_address": "192.168.1.101", "location": "1楼大厅", "status": "online", "toner_level": 78, "paper_level": 85, "supports_duplex": False},
            {"name": "HP LaserJet Pro M404dn", "brand": "HP", "model": "LaserJet Pro M404dn", "ip_address": "192.168.1.103", "location": "3楼财务部", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": True},
            {"name": "HP Color LaserJet MFP M479fdw", "brand": "HP", "model": "Color LaserJet MFP M479fdw", "ip_address": "192.168.1.104", "location": "4楼市场部", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_color": True, "supports_duplex": True, "toner_type": "CMYK"},
            {"name": "Canon iR-ADV C3530", "brand": "Canon", "model": "imageRUNNER ADVANCE C3530", "ip_address": "192.168.1.105", "location": "5楼高管区", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_color": True, "supports_duplex": True, "toner_type": "CMYK"},
            {"name": "Canon LBP226dw", "brand": "Canon", "model": "LBP226dw", "ip_address": "192.168.1.106", "location": "2楼研发部", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": True},
            {"name": "Epson WorkForce Pro WF-4830", "brand": "Epson", "model": "WorkForce Pro WF-4830", "ip_address": "192.168.1.107", "location": "3楼人力部", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_color": True, "supports_duplex": True, "toner_type": "CMYK"},
            {"name": "Epson EcoTank L15160", "brand": "Epson", "model": "EcoTank L15160", "ip_address": "192.168.1.108", "location": "1楼接待处", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_color": True},
            {"name": "Brother HL-L2350DW", "brand": "Brother", "model": "HL-L2350DW", "ip_address": "192.168.1.109", "location": "4楼设计部", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": True},
            {"name": "Brother MFC-L2750DW", "brand": "Brother", "model": "MFC-L2750DW", "ip_address": "192.168.1.110", "location": "2楼会议室A", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": True},
            {"name": "Kyocera ECOSYS P2040dw", "brand": "Kyocera", "model": "ECOSYS P2040dw", "ip_address": "192.168.1.111", "location": "5楼法务部", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": True},
            {"name": "Kyocera TASKalfa 2553ci", "brand": "Kyocera", "model": "TASKalfa 2553ci", "ip_address": "192.168.1.112", "location": "3楼运营部", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_color": True, "supports_duplex": True},
            {"name": "Ricoh IM C3000", "brand": "Ricoh", "model": "IM C3000", "ip_address": "192.168.1.113", "location": "4楼会议室B", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_color": True, "supports_duplex": True},
            {"name": "Xerox VersaLink C405", "brand": "Xerox", "model": "VersaLink C405", "ip_address": "192.168.1.114", "location": "1楼前台", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_color": True, "supports_duplex": True},
            {"name": "Samsung ProXpress M4580FX", "brand": "Samsung", "model": "ProXpress M4580FX", "ip_address": "192.168.1.115", "location": "2楼行政部", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": True},
            {"name": "HP LaserJet Enterprise M607", "brand": "HP", "model": "LaserJet Enterprise M607", "ip_address": "192.168.1.116", "location": "5楼数据中心", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": True},
            {"name": "Canon iR 1643iF", "brand": "Canon", "model": "imageRUNNER 1643iF", "ip_address": "192.168.1.117", "location": "1楼保安室", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": False},
            {"name": "Dell B3465dnf", "brand": "Dell", "model": "B3465dnf", "ip_address": "192.168.1.118", "location": "3楼库房", "status": "offline", "toner_level": 0, "paper_level": 0, "supports_duplex": True},
        ]

        printers = []
        for i, pd in enumerate(printer_data):
            printer = Printer(
                serial_number=f"SN-{pd['brand'][:2].upper()}-{1000 + i}",
                firmware_version=f"v{1 + i % 5}.{i % 10}.{i % 3}",
                mac_address=f"00:1A:2B:{i:02X}:{i*2:02X}:{i*3:02X}",
                last_seen_at=datetime.utcnow() if pd["status"] != "offline" else datetime.utcnow() - timedelta(hours=i + 1),
                total_pages_printed=(i + 1) * 1500,
                **pd,
            )
            printers.append(printer)
        db.add_all(printers)
        await db.flush()

        # === Status Logs (sample history per printer) ===
        import random
        for printer in printers:
            for h in range(24):
                log = PrinterStatusLog(
                    printer_id=printer.id,
                    status=random.choice(["online", "online", "online", "busy"]),
                    toner_level=max(0, printer.toner_level + random.randint(-5, 2)),
                    paper_level=max(0, printer.paper_level + random.randint(-10, 5)),
                    response_time_ms=random.randint(2, 150),
                    recorded_at=datetime.utcnow() - timedelta(hours=h),
                )
                db.add(log)

        # === Sample Alerts ===
        alert_scenarios = [
            (printers[5], "toner_low", "warning", "Canon LBP226dw black toner below 10%, please replace soon"),
            (printers[5], "paper_low", "info", "Canon LBP226dw tray 1 paper low"),
            (printers[13], "toner_empty", "critical", "Xerox VersaLink C405 black toner exhausted, printing stopped"),
            (printers[0], "paper_jam", "warning", "Paper jam detected in tray 1 of HP Laser MFP 136a - 1F"),
            (printers[7], "offline", "critical", "Epson EcoTank L15160 has been offline for over 2 hours"),
        ]
        for printer, atype, severity, message in alert_scenarios:
            alert = PrinterAlert(
                printer_id=printer.id,
                alert_type=atype,
                severity=severity,
                message=message,
                created_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 120)),
            )
            db.add(alert)

        # === Driver Packages ===
        driver_data = [
            # HP Laser MFP 136a - multiple platforms
            {"brand": "HP", "model": "Laser MFP 136a", "os_platform": "windows", "version": "2.14.2.28716", "file_size": 256 * 1024 * 1024, "storage_path": "drivers/hp/136a/win/2.14.2.28716.exe", "release_date": date(2024, 6, 15), "changelog": "修复 Windows 11 24H2 兼容性问题；提升网络打印稳定性", "download_count": 1250},
            {"brand": "HP", "model": "Laser MFP 136a", "os_platform": "windows", "version": "2.13.0.26542", "file_size": 240 * 1024 * 1024, "storage_path": "drivers/hp/136a/win/2.13.0.26542.exe", "release_date": date(2023, 11, 1), "changelog": "新增 Windows 11 支持；优化打印速度", "download_count": 890},
            {"brand": "HP", "model": "Laser MFP 136a", "os_platform": "macos", "version": "3.5.1", "file_size": 180 * 1024 * 1024, "storage_path": "drivers/hp/136a/mac/3.5.1.dmg", "release_date": date(2024, 5, 20), "changelog": "macOS 15 Sequoia 支持；修复扫描预览问题", "download_count": 680},
            {"brand": "HP", "model": "Laser MFP 136a", "os_platform": "macos", "version": "3.4.0", "file_size": 175 * 1024 * 1024, "storage_path": "drivers/hp/136a/mac/3.4.0.dmg", "release_date": date(2023, 10, 5), "changelog": "macOS 14 Sonoma 适配", "download_count": 520},
            {"brand": "HP", "model": "Laser MFP 136a", "os_platform": "linux", "version": "1.8.2", "file_size": 45 * 1024 * 1024, "storage_path": "drivers/hp/136a/linux/hplip-1.8.2.run", "release_date": date(2024, 3, 10), "changelog": "支持 Ubuntu 24.04 LTS; 修复 CUPS 2.4 兼容性", "download_count": 340},
            # Other models
            {"brand": "HP", "model": "LaserJet Pro M404dn", "os_platform": "windows", "version": "7.1.4", "file_size": 180 * 1024 * 1024, "storage_path": "drivers/hp/m404/win/7.1.4.exe", "release_date": date(2024, 1, 20), "download_count": 430},
            {"brand": "Canon", "model": "imageRUNNER ADVANCE C3530", "os_platform": "windows", "version": "3.12.0", "file_size": 320 * 1024 * 1024, "storage_path": "drivers/canon/c3530/win/3.12.0.exe", "release_date": date(2024, 2, 1), "download_count": 280},
            {"brand": "Canon", "model": "imageRUNNER ADVANCE C3530", "os_platform": "macos", "version": "2.8.1", "file_size": 200 * 1024 * 1024, "storage_path": "drivers/canon/c3530/mac/2.8.1.dmg", "release_date": date(2023, 12, 15), "download_count": 190},
            {"brand": "Epson", "model": "WorkForce Pro WF-4830", "os_platform": "windows", "version": "8.5.2", "file_size": 150 * 1024 * 1024, "storage_path": "drivers/epson/wf4830/win/8.5.2.exe", "release_date": date(2024, 4, 10), "download_count": 560},
            {"brand": "Brother", "model": "HL-L2350DW", "os_platform": "windows", "version": "1.9.0", "file_size": 120 * 1024 * 1024, "storage_path": "drivers/brother/hl2350/win/1.9.0.exe", "release_date": date(2024, 2, 28), "download_count": 410},
        ]
        for dd in driver_data:
            db.add(DriverPackage(**dd))

        # === Sample Scan Documents ===
        sample_docs = [
            {"filename": "2024年Q2财务报告扫描件.pdf", "file_size": 5 * 1024 * 1024, "mime_type": "application/pdf", "storage_path": "documents/zhangsan/q2_report.pdf", "page_count": 12, "tags": ["财务", "报告", "Q2"], "category": "Report", "user_id": normal_user.id},
            {"filename": "员工合同_张三.pdf", "file_size": 2 * 1024 * 1024, "mime_type": "application/pdf", "storage_path": "documents/zhangsan/contract.pdf", "page_count": 5, "tags": ["合同", "人事"], "category": "Contract", "user_id": normal_user.id},
            {"filename": "项目方案扫描.png", "file_size": 3 * 1024 * 1024, "mime_type": "image/png", "storage_path": "documents/zhangsan/proposal.png", "page_count": 1, "tags": ["项目", "方案"], "category": "Other", "user_id": normal_user.id},
        ]
        for sd in sample_docs:
            db.add(ScanDocument(**sd))

        await db.commit()
        print(f"Seed complete: 3 users, {len(printers)} printers, {len(driver_data)} driver packages, 3 documents")


if __name__ == "__main__":
    asyncio.run(seed())
