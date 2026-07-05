from __future__ import annotations
import random
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.diagnosis_conversation import DiagnosisConversation
from app.models.diagnosis_session import DiagnosisSession
from app.models.printer import Printer
from app.models.printer_status_log import PrinterStatusLog
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.diagnosis import (
    DiagnosisResultSchema,
    MessageCreate,
    MessageOut,
    PredictRequest,
    SessionCreate,
    SessionOut,
)
from app.utils.minio_client import minio_client
from app.utils.pdf_generator import generate_diagnosis_report

router = APIRouter(prefix="/diagnosis")


# ---------------------------------------------------------------------------
# Simple rule-based diagnosis engine (inline)
# ---------------------------------------------------------------------------

ERROR_CODE_REFERENCE = [
    {"code": "E001", "message": "Paper jam detected", "severity": "critical", "fix": "Open cover and remove jammed paper"},
    {"code": "E002", "message": "Toner empty", "severity": "critical", "fix": "Replace toner cartridge"},
    {"code": "E003", "message": "Toner low", "severity": "warning", "fix": "Prepare replacement toner"},
    {"code": "E004", "message": "Paper tray empty", "severity": "warning", "fix": "Refill paper tray"},
    {"code": "E005", "message": "Fuser temperature error", "severity": "critical", "fix": "Allow printer to cool down, then restart"},
    {"code": "E006", "message": "Drum unit worn", "severity": "warning", "fix": "Replace drum unit soon"},
    {"code": "E007", "message": "Network connection lost", "severity": "warning", "fix": "Check network cable and router"},
    {"code": "E008", "message": "Unsupported paper size", "severity": "info", "fix": "Use supported paper size (A4/Letter)"},
    {"code": "E009", "message": "Scanner error", "severity": "critical", "fix": "Restart printer; contact service if persistent"},
    {"code": "E010", "message": "Print head alignment needed", "severity": "info", "fix": "Run print head alignment from printer menu"},
]

# Keyword-to-diagnosis mapping
DIAGNOSIS_RULES: list[dict] = [
    {
        "keywords": ["paper", "jam", "stuck", "卡纸", "paper jam"],
        "fault_type": "卡纸 (Paper Jam)",
        "root_cause": "纸张在进纸通道或出纸通道中卡住，可能是纸张质量问题、纸张受潮或异物阻挡。",
        "severity": "medium",
        "steps": [
            "关闭打印机电源，拔掉电源线",
            "打开前盖和后盖，检查卡纸位置",
            "沿出纸方向缓慢拉出卡住的纸张",
            "检查辊轴上是否有残留纸屑",
            "重新装入纸张，关闭所有盖板",
            "接通电源，打印测试页确认恢复正常",
        ],
        "parts": [],
        "safety": ["关闭电源后再操作", "不要用力拉扯纸张以免损坏滚轴"],
        "confidence": 0.85,
    },
    {
        "keywords": ["toner", "cartridge", "硒鼓", "碳粉", "墨粉", "faint", "淡"],
        "fault_type": "碳粉问题 (Toner Issue)",
        "root_cause": "碳粉不足、硒鼓老化或碳粉分布不均匀导致打印质量下降。",
        "severity": "high",
        "steps": [
            "检查碳粉余量",
            "取出硒鼓，轻轻摇晃使碳粉均匀分布",
            "如果碳粉耗尽，更换新硒鼓",
            "运行打印机清洁页面",
            "打印测试页验证打印质量",
        ],
        "parts": ["硒鼓 (Toner Cartridge)"],
        "safety": ["更换硒鼓时避免接触碳粉", "旧硒鼓按当地环保规定回收"],
        "confidence": 0.80,
    },
    {
        "keywords": ["offline", "off line", "离线", "disconnect", "连接"],
        "fault_type": "连接问题 (Connectivity Issue)",
        "root_cause": "打印机与网络或电脑的连接中断，可能是网络配置问题、USB线松动或IP地址变更。",
        "severity": "high",
        "steps": [
            "检查USB线或网线是否牢固连接",
            "确认打印机电源已开启",
            "检查打印机IP地址是否正确",
            "重新启动打印机和路由器",
            "在电脑上重新添加打印机",
            "更新打印机固件到最新版本",
        ],
        "parts": [],
        "safety": [],
        "confidence": 0.75,
    },
    {
        "keywords": ["stripe", "line", "条纹", "line", "streak"],
        "fault_type": "打印条纹 (Print Streaks)",
        "root_cause": "打印头脏污、硒鼓损坏或转印带问题导致页面出现条纹。",
        "severity": "medium",
        "steps": [
            "运行打印机内置的清洁程序",
            "检查硒鼓表面是否有划痕",
            "清洁打印头（喷墨打印机）",
            "如果条纹规律出现，更换硒鼓",
            "检查转印带是否需要清洁或更换",
        ],
        "parts": ["清洁套件", "硒鼓"],
        "safety": ["待打印机冷却后再清洁内部组件"],
        "confidence": 0.70,
    },
    {
        "keywords": ["noise", "noisy", "噪音", "响声", "grinding"],
        "fault_type": "异常噪音 (Abnormal Noise)",
        "root_cause": "打印机内部齿轮磨损、异物卡入或马达故障导致运行时发出异常噪音。",
        "severity": "medium",
        "steps": [
            "关闭打印机电源",
            "检查打印机内部是否有异物",
            "观察噪音来源（进纸区、出纸区、扫描头）",
            "清理并润滑齿轮和导轨",
            "如噪音持续，联系专业维修",
        ],
        "parts": ["润滑油", "齿轮组件"],
        "safety": ["务必断电操作", "避免触碰加热组件"],
        "confidence": 0.65,
    },
]


def diagnose(message: str) -> DiagnosisResultSchema:
    """Simple rule-based diagnosis engine."""
    message_lower = message.lower()

    best_match = None
    best_score = 0

    for rule in DIAGNOSIS_RULES:
        score = sum(1 for kw in rule["keywords"] if kw.lower() in message_lower)
        if score > best_score:
            best_score = score
            best_match = rule

    if best_match and best_score > 0:
        return DiagnosisResultSchema(
            fault_type=best_match["fault_type"],
            root_cause=best_match["root_cause"],
            severity=best_match["severity"],
            steps=best_match["steps"],
            parts=best_match["parts"],
            safety=best_match["safety"],
            confidence=best_match["confidence"],
        )

    # Default fallback
    return DiagnosisResultSchema(
        fault_type="未知故障 (Unknown Issue)",
        root_cause="无法根据当前描述自动确定故障原因。建议提供更多症状细节，或参考打印机用户手册。",
        severity="low",
        steps=[
            "重新启动打印机",
            "检查打印机面板是否有错误提示",
            "查阅打印机用户手册获取帮助",
            "联系技术支持人员",
        ],
        parts=[],
        safety=["在进行任何维修前请关闭打印机电源"],
        confidence=0.3,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new diagnosis session."""
    session = DiagnosisSession(
        user_id=current_user.id,
        printer_id=body.printer_id,
        session_title=body.title or "New Diagnosis",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    session.messages = None

    return session


@router.get("/sessions", response_model=PaginatedResponse[SessionOut])
async def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's diagnosis sessions."""
    query = (
        select(DiagnosisSession)
        .where(DiagnosisSession.user_id == current_user.id)
        .order_by(DiagnosisSession.updated_at.desc())
    )
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sessions = list(result.scalars().all())
    # Avoid lazy-load: set messages to None for list view
    for s in sessions:
        s.messages = None

    return PaginatedResponse(
        items=sessions,
        total=len(sessions),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.get("/sessions/{id}", response_model=SessionOut)
async def get_session(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get session with all messages."""
    try:
        session_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    result = await db.execute(
        select(DiagnosisSession)
        .where(
            DiagnosisSession.id == session_id,
            DiagnosisSession.user_id == current_user.id,
        )
        .options(selectinload(DiagnosisSession.messages))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return session


@router.post("/sessions/{id}/messages")
async def send_message(
    id: str,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in a diagnosis session and get AI response."""
    try:
        session_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    result = await db.execute(
        select(DiagnosisSession).where(
            DiagnosisSession.id == session_id,
            DiagnosisSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Get current step number
    step_result = await db.execute(
        select(DiagnosisConversation)
        .where(DiagnosisConversation.session_id == session_id)
        .order_by(DiagnosisConversation.step_number.desc())
        .limit(1)
    )
    last_msg = step_result.scalar_one_or_none()
    next_step = (last_msg.step_number or 0) + 1 if last_msg else 1

    # Create user message
    user_msg = DiagnosisConversation(
        session_id=session_id,
        role="user",
        message=body.message,
        step_number=next_step,
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Run diagnosis
    diagnosis_result = diagnose(body.message)

    # Create assistant message
    assistant_msg = DiagnosisConversation(
        session_id=session_id,
        role="assistant",
        message=f"诊断结果：{diagnosis_result.fault_type}\n\n"
                f"根本原因：{diagnosis_result.root_cause}\n\n"
                f"修复步骤：\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(diagnosis_result.steps)),
        diagnosis_result=diagnosis_result.model_dump(),
        step_number=next_step,
    )
    db.add(assistant_msg)

    # Update session
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(assistant_msg)

    return {
        "user_message": MessageOut.model_validate(user_msg),
        "assistant_message": MessageOut.model_validate(assistant_msg),
    }


@router.get("/sessions/{id}/report")
async def generate_report(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a PDF diagnosis report and return download URL."""
    try:
        session_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    result = await db.execute(
        select(DiagnosisSession)
        .where(
            DiagnosisSession.id == session_id,
            DiagnosisSession.user_id == current_user.id,
        )
        .options(
            selectinload(DiagnosisSession.messages),
            selectinload(DiagnosisSession.printer),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Prepare data for PDF
    session_data = {
        "title": session.session_title,
        "created_at": session.created_at.isoformat(),
        "printer_info": {
            "name": session.printer.name if session.printer else "未知",
            "model": session.printer.model if session.printer else "未知",
        },
        "conclusions": session.resolution_summary or "暂无诊断结论",
        "recommendations": "建议联系IT支持或服务中心进一步检修。" if not session.resolution_summary else "",
    }

    messages_data = [
        {
            "role": msg.role,
            "content": msg.message,
            "timestamp": msg.created_at.isoformat() if msg.created_at else "",
        }
        for msg in sorted(session.messages, key=lambda m: m.step_number or 0)
    ]

    # Generate PDF
    pdf_bytes = generate_diagnosis_report(session_data, messages_data)

    # Upload to MinIO
    import os
    import tempfile

    report_object = f"reports/diagnosis/{session_id}.pdf"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        minio_client.upload_file(report_object, tmp_path, "application/pdf")
    finally:
        os.unlink(tmp_path)

    # Return presigned URL
    url = minio_client.get_presigned_url(report_object, expires=86400)
    return {
        "url": url,
        "filename": f"diagnosis_report_{session.session_title}.pdf",
    }


@router.get("/error-codes")
async def get_error_codes():
    """Return error code reference list."""
    return {"error_codes": ERROR_CODE_REFERENCE}


@router.post("/predict")
async def predict_failure(
    body: PredictRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze status log history and return risk assessment."""
    try:
        printer_id = uuid.UUID(body.printer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid printer ID format",
        )

    # Get printer info
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()

    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    # Get recent status logs
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(PrinterStatusLog)
        .where(
            PrinterStatusLog.printer_id == printer_id,
            PrinterStatusLog.recorded_at >= cutoff,
        )
        .order_by(PrinterStatusLog.recorded_at.desc())
        .limit(200)
    )
    logs = result.scalars().all()

    error_count = sum(1 for log in logs if log.status == "error")
    offline_count = sum(1 for log in logs if log.status == "offline")

    # Simple risk calculation
    total = len(logs) or 1
    error_rate = error_count / total
    offline_rate = offline_count / total

    if error_rate > 0.1:
        risk_level = "high"
        risk_message = "检测到较高的错误率，建议尽快安排维护。"
    elif error_rate > 0.05:
        risk_level = "medium"
        risk_message = "打印机偶尔出现错误，建议定期检查。"
    elif offline_rate > 0.1:
        risk_level = "medium"
        risk_message = "打印机连接不稳定，请检查网络。"
    else:
        risk_level = "low"
        risk_message = "打印机状态良好，未发现异常。"

    # Check toner level trends
    avg_toner = sum(log.toner_level for log in logs if log.toner_level is not None) / max(
        sum(1 for log in logs if log.toner_level is not None), 1
    )

    toner_warning = None
    if avg_toner < 10:
        toner_warning = "碳粉即将耗尽，请立即更换。"
    elif avg_toner < 20:
        toner_warning = "碳粉量较低，请准备备用硒鼓。"

    return {
        "printer_id": str(printer_id),
        "printer_name": printer.name,
        "risk_level": risk_level,
        "risk_message": risk_message,
        "error_rate": round(error_rate * 100, 1),
        "offline_rate": round(offline_rate * 100, 1),
        "avg_toner_level": round(avg_toner, 1) if avg_toner > 0 else None,
        "toner_warning": toner_warning,
        "total_logs_analyzed": total,
        "predicted_at": datetime.now(timezone.utc).isoformat(),
    }
