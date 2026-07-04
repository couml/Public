from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_diagnosis_report(session: dict, messages: list[dict]) -> bytes:
    """
    Generate a PDF diagnosis report using reportlab.

    Args:
        session: Dict with keys like title, created_at, printer_info
        messages: List of dicts with role, content, timestamp

    Returns:
        PDF as bytes
    """
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=25 * mm,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6,
    )
    normal_style = styles["Normal"]
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor="#888888",
    )

    story = []

    # Title
    story.append(Paragraph("AI 故障诊断报告", title_style))
    story.append(Spacer(1, 6 * mm))

    # Session info
    story.append(Paragraph("会话信息", heading_style))
    session_title = session.get("title", "未知")
    session_date = session.get("created_at", datetime.now()).strftime("%Y-%m-%d %H:%M") if session.get("created_at") else datetime.now().strftime("%Y-%m-%d %H:%M")
    printer_info = session.get("printer_info", {})

    info_data = [
        ["会话标题:", str(session_title)],
        ["日期:", str(session_date)],
        ["打印机:", str(printer_info.get("name", "未知"))],
        ["型号:", str(printer_info.get("model", "未知"))],
    ]
    info_table = Table(info_data, colWidths=[80, 300])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6 * mm))

    # Diagnosis conclusions
    story.append(Paragraph("诊断结论", heading_style))
    conclusions = session.get("conclusions", "")
    if conclusions:
        story.append(Paragraph(str(conclusions), normal_style))
    else:
        story.append(Paragraph("暂无诊断结论", normal_style))
    story.append(Spacer(1, 6 * mm))

    # Conversation transcript
    story.append(Paragraph("会话记录", heading_style))
    for i, msg in enumerate(messages):
        role_label = "用户" if msg.get("role") == "user" else "AI 助手"
        timestamp = msg.get("timestamp", "")
        content = msg.get("content", "")
        story.append(Paragraph(
            f"<b>[{role_label}]</b> {timestamp}<br/>{content}",
            normal_style,
        ))
        story.append(Spacer(1, 2 * mm))

    story.append(Spacer(1, 6 * mm))

    # Repair recommendations
    story.append(Paragraph("维修建议", heading_style))
    recommendations = session.get("recommendations", "")
    if recommendations:
        story.append(Paragraph(str(recommendations), normal_style))
    else:
        story.append(Paragraph("暂无维修建议", normal_style))

    # Footer with page numbers
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2,
            12 * mm,
            f"第 {canvas.getPageNumber()} 页",
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    buffer.seek(0)
    return buffer.read()
