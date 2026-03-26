from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
BRAND_DARK = colors.HexColor("#1A2E44")   # dark navy
BRAND_MID  = colors.HexColor("#2E6DA4")   # medium blue
BRAND_LIGHT = colors.HexColor("#E8F0F8")  # very light blue tint
GRAY_TEXT  = colors.HexColor("#555555")
RULE_COLOR = colors.HexColor("#CCCCCC")


def _build_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles["doc_title"] = ParagraphStyle(
        "doc_title",
        parent=base["Normal"],
        fontSize=20,
        textColor=BRAND_DARK,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["doc_subtitle"] = ParagraphStyle(
        "doc_subtitle",
        parent=base["Normal"],
        fontSize=11,
        textColor=BRAND_MID,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    styles["doc_date"] = ParagraphStyle(
        "doc_date",
        parent=base["Normal"],
        fontSize=9,
        textColor=GRAY_TEXT,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    styles["section_heading"] = ParagraphStyle(
        "section_heading",
        parent=base["Normal"],
        fontSize=13,
        textColor=BRAND_DARK,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=4,
    )
    styles["field_label"] = ParagraphStyle(
        "field_label",
        parent=base["Normal"],
        fontSize=9,
        textColor=BRAND_MID,
        fontName="Helvetica-Bold",
        spaceBefore=6,
        spaceAfter=1,
    )
    styles["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontSize=10,
        textColor=colors.black,
        fontName="Helvetica",
        leading=14,
        spaceAfter=2,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        parent=base["Normal"],
        fontSize=10,
        textColor=colors.black,
        fontName="Helvetica",
        leading=14,
        leftIndent=14,
        spaceAfter=1,
    )
    styles["footer"] = ParagraphStyle(
        "footer",
        parent=base["Normal"],
        fontSize=8,
        textColor=GRAY_TEXT,
        fontName="Helvetica",
        alignment=TA_CENTER,
    )

    return styles


def _safe(val, fallback="Not available"):
    if val is None:
        return fallback
    val = str(val).strip()
    return val if val else fallback


def _bullet_list(items, styles):
    """Return a list of Paragraph objects for a bullet list."""
    elements = []
    for item in items:
        text = _safe(item, "")
        if text and text != "Not available":
            elements.append(Paragraph(f"\u2022  {text}", styles["bullet"]))
    return elements


def generate_pdf(result: dict, company_url: str, contact_name: str) -> bytes:
    """
    Generate a PDF report from the research result dict.
    Returns the PDF as bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
    )

    styles = _build_styles()
    story = []

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    story.append(Paragraph("Meazure Sales Intelligence Report", styles["doc_title"]))

    contact_data = result.get("contact", {})
    company_data = result.get("company", {})

    company_name = _safe(company_data.get("name"), company_url)
    contact_display = _safe(contact_data.get("name"), contact_name)

    story.append(Paragraph(f"{contact_display}  &nbsp;|&nbsp;  {company_name}", styles["doc_subtitle"]))
    story.append(Paragraph(f"Generated {date.today().strftime('%B %d, %Y')}", styles["doc_date"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_MID, spaceAfter=10))

    # ------------------------------------------------------------------
    # Section 1: Contact Intel
    # ------------------------------------------------------------------
    story.append(Paragraph("1.  Contact Intel", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4))

    fields = [
        ("Name", contact_data.get("name")),
        ("Title", contact_data.get("title")),
        ("Responsibilities", contact_data.get("responsibilities")),
        ("Professional Interests", contact_data.get("interests")),
        ("Recent Activity", contact_data.get("recent_activity")),
    ]
    for label, val in fields:
        story.append(Paragraph(label, styles["field_label"]))
        story.append(Paragraph(_safe(val), styles["body"]))

    additional = contact_data.get("suggested_additional_contacts", [])
    if additional:
        story.append(Spacer(1, 6))
        story.append(Paragraph("Suggested Additional Contacts", styles["field_label"]))
        for ac in additional:
            name = _safe(ac.get("name"), "Unknown")
            title = _safe(ac.get("likely_title"), "")
            why = _safe(ac.get("why_relevant"), "")
            line = f"<b>{name}</b>"
            if title:
                line += f" — {title}"
            if why:
                line += f":  {why}"
            story.append(Paragraph(f"\u2022  {line}", styles["bullet"]))

    # ------------------------------------------------------------------
    # Section 2: Company Intel
    # ------------------------------------------------------------------
    story.append(Spacer(1, 8))
    story.append(Paragraph("2.  Company Intel", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4))

    company_fields = [
        ("Company Name", company_data.get("name")),
        ("Website", company_data.get("website")),
        ("Industry", company_data.get("industry")),
        ("Description", company_data.get("description")),
        ("Goals & Growth Areas", company_data.get("goals_and_growth_areas")),
        ("Challenges", company_data.get("challenges")),
        ("Stay-in-Touch Trigger", company_data.get("stay_in_touch")),
    ]
    for label, val in company_fields:
        story.append(Paragraph(label, styles["field_label"]))
        story.append(Paragraph(_safe(val), styles["body"]))

    news = company_data.get("recent_news", [])
    if news:
        story.append(Paragraph("Recent News", styles["field_label"]))
        story.extend(_bullet_list(news, styles))

    # ------------------------------------------------------------------
    # Section 3: Conversation Starters
    # ------------------------------------------------------------------
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.  Conversation Starters", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4))

    conv = result.get("conversation_starters", {})
    pain_points = conv.get("anticipated_pain_points", [])
    if pain_points:
        story.append(Paragraph("Anticipated Pain Points", styles["field_label"]))
        story.extend(_bullet_list(pain_points, styles))

    questions = conv.get("suggested_questions", [])
    if questions:
        story.append(Spacer(1, 4))
        story.append(Paragraph("Suggested Questions for the Call", styles["field_label"]))
        for i, q in enumerate(questions, 1):
            story.append(Paragraph(f"{i}.  {_safe(q)}", styles["bullet"]))

    # ------------------------------------------------------------------
    # Section 4: Meazure Opportunity Map
    # ------------------------------------------------------------------
    story.append(Spacer(1, 8))
    story.append(Paragraph("4.  Meazure Opportunity Map", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=6))

    opp_map = result.get("opportunity_map", [])
    if opp_map:
        # Build a table
        table_data = [
            [
                Paragraph("<b>Meazure Service</b>", styles["body"]),
                Paragraph("<b>Relevance</b>", styles["body"]),
                Paragraph("<b>Talking Point</b>", styles["body"]),
            ]
        ]
        for entry in opp_map:
            service = _safe(entry.get("meazure_service"), "")
            relevance = _safe(entry.get("relevance"), "")
            talking = _safe(entry.get("talking_point"), "")
            table_data.append([
                Paragraph(service, styles["body"]),
                Paragraph(relevance, styles["body"]),
                Paragraph(talking, styles["body"]),
            ])

        col_widths = [1.6 * inch, 2.0 * inch, 3.0 * inch]
        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_LIGHT),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_DARK),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.4, RULE_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
    else:
        story.append(Paragraph("No opportunity mapping data available.", styles["body"]))

    # ------------------------------------------------------------------
    # Footer via onLaterPages / onFirstPage via a frame
    # We use a simple bottom note appended to story instead.
    # ------------------------------------------------------------------
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4))
    story.append(Paragraph("Confidential — Meazure Learning", styles["footer"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
