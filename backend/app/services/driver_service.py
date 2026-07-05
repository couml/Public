from __future__ import annotations
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DriverDownloadLog, DriverPackage


async def list_drivers(
    db: AsyncSession,
    brand: str | None = None,
    model: str | None = None,
    os: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[DriverPackage], int]:
    conditions = [DriverPackage.is_active == True]
    if brand:
        conditions.append(DriverPackage.brand == brand)
    if model:
        conditions.append(DriverPackage.model == model)
    if os:
        conditions.append(DriverPackage.os_platform == os)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            or_(
                DriverPackage.brand.ilike(pattern),
                DriverPackage.model.ilike(pattern),
                DriverPackage.version.ilike(pattern),
            )
        )

    base_query = select(DriverPackage).where(and_(*conditions))

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        base_query
        .order_by(DriverPackage.release_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    drivers = list(result.scalars().all())

    return drivers, total


async def get_driver_by_id(
    db: AsyncSession, driver_id: uuid.UUID
) -> DriverPackage:
    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == driver_id)
    )
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


async def get_brands(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(DriverPackage.brand)
        .where(DriverPackage.is_active == True)
        .distinct()
        .order_by(DriverPackage.brand)
    )
    return list(result.scalars().all())


async def get_models(db: AsyncSession, brand: str) -> list[str]:
    result = await db.execute(
        select(DriverPackage.model)
        .where(
            and_(
                DriverPackage.is_active == True,
                DriverPackage.brand == brand,
            )
        )
        .distinct()
        .order_by(DriverPackage.model)
    )
    return list(result.scalars().all())


async def get_driver_versions(
    db: AsyncSession, driver_id: uuid.UUID
) -> list[DriverPackage]:
    driver = await get_driver_by_id(db, driver_id)

    result = await db.execute(
        select(DriverPackage).where(
            and_(
                DriverPackage.brand == driver.brand,
                DriverPackage.model == driver.model,
                DriverPackage.os_platform == driver.os_platform,
                DriverPackage.is_active == True,
            )
        ).order_by(DriverPackage.release_date.desc())
    )
    return list(result.scalars().all())


async def record_download(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    driver_id: uuid.UUID,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    driver = await get_driver_by_id(db, driver_id)
    driver.download_count += 1

    log_entry = DriverDownloadLog(
        user_id=user_id,
        driver_id=driver_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log_entry)
    await db.commit()


async def get_hp136a_page(db: AsyncSession) -> dict:
    return {
        "printer": {
            "brand": "HP",
            "model": "LaserJet Pro MFP M136a",
            "type": "黑白激光多功能一体机",
            "functions": ["打印", "复印", "扫描"],
            "print_speed": "20页/分钟 (A4)",
            "resolution": "1200 x 1200 dpi",
            "paper_capacity": "150页进纸盒",
            "monthly_duty_cycle": "8000页",
        },
        "drivers": [
            {
                "id": str(uuid.uuid4()),
                "os_platform": "windows",
                "os_label": "Windows 11 / 10 / 8.1 / 7",
                "version": "15.0.15300.404",
                "file_size": 235_000_000,
                "release_date": "2025-06-15",
                "download_url": "/api/v1/drivers/download/windows-latest",
                "type": "Full Feature Driver",
            },
            {
                "id": str(uuid.uuid4()),
                "os_platform": "windows",
                "os_label": "Windows 11 ARM64",
                "version": "15.0.15200.231",
                "file_size": 198_000_000,
                "release_date": "2025-03-20",
                "download_url": "/api/v1/drivers/download/windows-arm64",
                "type": "Full Feature Driver",
            },
            {
                "id": str(uuid.uuid4()),
                "os_platform": "macos",
                "os_label": "macOS 14 Sonoma / 13 Ventura / 12 Monterey",
                "version": "5.1.8",
                "file_size": 156_000_000,
                "release_date": "2025-05-10",
                "download_url": "/api/v1/drivers/download/macos-latest",
                "type": "HP Easy Start",
            },
            {
                "id": str(uuid.uuid4()),
                "os_platform": "linux",
                "os_label": "Linux (deb/rpm)",
                "version": "3.22.10",
                "file_size": 42_000_000,
                "release_date": "2025-04-01",
                "download_url": "/api/v1/drivers/download/linux-latest",
                "type": "HPLIP",
            },
        ],
        "manuals": [
            {
                "title": "HP LaserJet Pro MFP M136a 用户指南 (中文)",
                "url": "/api/v1/drivers/manuals/m136a-user-guide-zh.pdf",
                "size": "4.2 MB",
            },
            {
                "title": "HP LaserJet Pro MFP M136a User Guide (EN)",
                "url": "/api/v1/drivers/manuals/m136a-user-guide-en.pdf",
                "size": "3.8 MB",
            },
            {
                "title": "HP LaserJet Pro MFP M136a 安装指南",
                "url": "/api/v1/drivers/manuals/m136a-setup-zh.pdf",
                "size": "1.5 MB",
            },
            {
                "title": "HP LaserJet Pro MFP M136a 故障排除指南",
                "url": "/api/v1/drivers/manuals/m136a-troubleshoot-zh.pdf",
                "size": "2.1 MB",
            },
        ],
        "faqs": [
            {
                "question": "M136a 如何在 Windows 11 上安装驱动？",
                "answer": (
                    "1. 从本站下载 Windows 全功能驱动程序\n"
                    "2. 运行安装程序，选择「USB 连接」或「网络连接」\n"
                    "3. 按照向导完成安装\n"
                    "4. 安装完成后打印测试页确认"
                ),
            },
            {
                "question": "M136a 硒鼓型号是什么？",
                "answer": (
                    "M136a 使用 HP 136A 黑色原装硒鼓（W1360A / 136X）。\n"
                    "标准容量印量约 1,150 页，高容量（136X）约 2,600 页。"
                ),
            },
            {
                "question": "打印出来的纸张有黑色竖线怎么办？",
                "answer": (
                    "可能原因：\n"
                    "1. 硒鼓感光鼓有划痕或污染 — 更换硒鼓\n"
                    "2. 定影膜上有污渍 — 清洁定影组件\n"
                    "3. 充电辊污染 — 清洁或更换充电辊"
                ),
            },
            {
                "question": "M136a 如何连接Wi-Fi打印？",
                "answer": (
                    "M136a 标准型号仅支持 USB 连接，不支持 Wi-Fi。\n"
                    "如需无线打印，请选购 M136w 或 M136nw 型号，\n"
                    "或通过连接打印服务器实现网络共享。"
                ),
            },
            {
                "question": "如何解决卡纸问题？",
                "answer": (
                    "1. 关闭打印机电源\n"
                    "2. 打开前盖和硒鼓舱门\n"
                    "3. 轻轻拉出卡住的纸张（注意方向，避免撕裂）\n"
                    "4. 检查进纸盘是否有异物\n"
                    "5. 重新装好硒鼓，关闭舱门，开机测试"
                ),
            },
            {
                "question": "M136a 支持手机打印吗？",
                "answer": (
                    "M136a 支持通过 HP Smart 应用进行手机打印（需USB OTG连接）。\n"
                    "对于无线型号（M136w/M136nw），可使用 HP Smart、Apple AirPrint、Mopria Print Service。"
                ),
            },
        ],
        "install_guides": {
            "windows": (
                "## Windows 安装步骤\n\n"
                "1. 下载 Windows 驱动程序\n"
                "2. 断开打印机 USB 线缆\n"
                "3. 运行下载的安装程序\n"
                "4. 当安装程序提示时，连接 USB 线缆\n"
                "5. 等待驱动安装完成\n"
                "6. 打印测试页验证\n\n"
                "**注意：** 安装前请先卸载旧版驱动"
            ),
            "macos": (
                "## macOS 安装步骤\n\n"
                "1. 下载 HP Easy Start 或对应版本的驱动\n"
                "2. 打开下载的 .dmg 文件\n"
                "3. 运行 HP Easy Start\n"
                "4. 选择您的打印机型号（如已连接USB会自动识别）\n"
                "5. 按照向导完成安装\n"
                "6. 在「系统设置 > 打印机与扫描仪」中确认"
            ),
            "linux": (
                "## Linux 安装步骤\n\n"
                "### Ubuntu / Debian\n"
                "```bash\n"
                "sudo apt install hplip hplip-gui\n"
                "hp-setup\n"
                "```\n\n"
                "### Fedora / RHEL\n"
                "```bash\n"
                "sudo dnf install hplip hplip-gui\n"
                "hp-setup\n"
                "```\n\n"
                "### 手动安装\n"
                "从本站下载 HPLIP 包，解压后运行：\n"
                "```bash\n"
                "./configure --with-hpppdir=/usr/share/ppd/HP\n"
                "make && sudo make install\n"
                "```"
            ),
        },
        "related_printers": [
            {"model": "HP LaserJet Pro MFP M136w", "difference": "支持 Wi-Fi"},
            {"model": "HP LaserJet Pro MFP M136nw", "difference": "支持 Wi-Fi + 以太网"},
            {"model": "HP Laser 107a", "difference": "单功能打印"},
            {"model": "HP Laser MFP 1188a", "difference": "三合一 + 更高印速"},
            {"model": "HP LaserJet Pro MFP M227fdw", "difference": "四合一 + 自动双面"},
        ],
    }
