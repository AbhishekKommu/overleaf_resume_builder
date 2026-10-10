import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle)

BODY = 9.5
PAGE_W = A4[0] - 36 * mm - 12  # usable width (frame has 6pt padding per side)


def _styles():
    base = dict(fontName="Times-Roman", fontSize=BODY, leading=BODY * 1.3)
    return {
        "name": ParagraphStyle("name", fontName="Times-Bold", fontSize=20, leading=24, alignment=TA_CENTER),
        "contact": ParagraphStyle("contact", alignment=TA_CENTER, **base),
        "section": ParagraphStyle("section", fontName="Times-Bold", fontSize=11, leading=14, spaceBefore=9),
        "bold": ParagraphStyle("bold", fontName="Times-Bold", fontSize=BODY, leading=BODY * 1.3),
        "left": ParagraphStyle("left", **base),
        "right": ParagraphStyle("right", alignment=TA_RIGHT, **base),
        "body": ParagraphStyle("body", alignment=TA_JUSTIFY, **base),
        "indent": ParagraphStyle("indent", alignment=TA_JUSTIFY, leftIndent=8, **base),
        "bullet": ParagraphStyle("bullet", alignment=TA_JUSTIFY, leftIndent=10, bulletIndent=0, spaceAfter=2, **base),
    }


def _e(text):
    return escape(text or "")


def _multiline(text):
    return "<br/>".join(_e(line.strip()) for line in (text or "").splitlines() if line.strip())


def _section(story, st, label):
    story.append(Paragraph(label.upper(), st["section"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=4))


def _lines(text):
    out = []
    for line in (text or "").splitlines():
        line = line.strip().lstrip("-\u2022* ").strip()
        if line:
            out.append(line)
    return out


def _row(left, right, st, left_style="left", right_style="right"):
    t = Table([[Paragraph(left, st[left_style]), Paragraph(right, st[right_style])]],
              colWidths=[PAGE_W * 0.75, PAGE_W * 0.25])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def build_pdf(content):
    """Return PDF bytes for a resume content dict (Overleaf/LaTeX-style layout)."""
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title=content.get("name") or "Resume")
    story = [Paragraph(_e(content.get("name")) or "YOUR NAME", st["name"])]

    parts = [_e(content.get(k)) for k in ("phone", "email") if content.get(k)]
    for key, label in (("linkedin", "LinkedIn"), ("github", "GitHub")):
        url = (content.get(key) or "").strip()
        if url:
            if not url.startswith("http"):
                url = "https://" + url
            parts.append(f'<link href="{_e(url)}" color="#1a3a6b">{label}</link>')
    if parts:
        story.append(Paragraph("  \u2014  ".join(parts), st["contact"]))

    if content.get("objective"):
        _section(story, st, "Objective")
        story.append(Paragraph(_e(content["objective"]), st["body"]))

    if content.get("education"):
        _section(story, st, "Education")
        for e in content["education"]:
            story.append(_row(f"<b>{_e(e.get('degree'))}</b>", _e(e.get("date")), st))
            if e.get("institution"):
                story.append(Paragraph(_e(e["institution"]), st["left"]))
            if e.get("detail") or e.get("location"):
                story.append(_row(_e(e.get("detail")), _e(e.get("location")), st))
            story.append(Spacer(1, 3))

    skills = [s for s in content.get("skills", []) if s.get("label") or s.get("value")]
    if skills:
        _section(story, st, "Skills")
        rows = [[Paragraph(_e(s.get("label")), st["bold"]), Paragraph(_multiline(s.get("value")), st["left"])] for s in skills]
        t = Table(rows, colWidths=[PAGE_W * 0.27, PAGE_W * 0.73])
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(t)

    exp = _lines(content.get("experience"))
    if exp:
        _section(story, st, "Project Experience")
        for line in exp:
            story.append(Paragraph(_e(line), st["bullet"], bulletText="\u2022"))

    projects = [p for p in content.get("projects", []) if p.get("name") or p.get("description")]
    if projects:
        _section(story, st, "Projects")
        for p in projects:
            story.append(Paragraph(f"<b>{_e(p.get('name'))}</b>", st["left"]))
            if p.get("description"):
                story.append(Paragraph(_e(p["description"]), st["indent"]))
            story.append(Spacer(1, 3))

    if content.get("declaration"):
        _section(story, st, "Declaration")
        story.append(Paragraph(_e(content["declaration"]), st["bullet"], bulletText="\u2022"))

    doc.build(story)
    return buf.getvalue()
