"""PDF Report Exporter using ReportLab (FR-062, Spec §49.11)."""
from __future__ import annotations

import html
import io
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _esc(value: Any) -> str:
    """Escape user content for ReportLab Paragraph (mini-HTML)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for k in ("text", "summary", "description", "interpretation", "meaning", "full_text", "theme"):
            if k in value and isinstance(value[k], (str, int, float)):
                return html.escape(str(value[k]), quote=False)
        return html.escape(str({k: str(v) for k, v in value.items()}), quote=False)
    if isinstance(value, (list, tuple)):
        return html.escape(", ".join(str(v) for v in value), quote=False)
    text = str(value)
    # ReportLab Paragraph understands a small HTML subset; escape first.
    return html.escape(text, quote=False).replace("\n", "<br/>")


def _pct(value: Any, default: str = "—") -> str:
    if value is None or value == "":
        return default
    try:
        return f"{float(value)}%"
    except (TypeError, ValueError):
        return _esc(value)


def _join(items: Any) -> str:
    if not items:
        return "—"
    if isinstance(items, str):
        return _esc(items)
    return _esc(", ".join(str(x) for x in items))


def _header_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#94A3B8"))
    canvas.drawString(40, 30, "MysticLens Spiritual Intelligence  •  Interpretive guidance — not medical, legal or financial advice.")
    canvas.drawRightString(letter[0] - 40, 30, f"Page {doc.page}")
    canvas.restoreState()


def export_report_to_pdf(report: Dict[str, Any]) -> bytes:
    """Render a structured reading report into an in-memory PDF document."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=44,
        bottomMargin=44,
        title=str(report.get("title", "Reading Report"))[:80],
        author="MysticLens",
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#312E81")  # Deep Indigo
    gold_color = colors.HexColor("#B45309")  # Amber Gold
    dark_slate = colors.HexColor("#1E293B")
    muted_text = colors.HexColor("#64748B")
    light_bg = colors.HexColor("#F8FAFC")
    border_grey = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle("DocTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=21, leading=25, textColor=primary_color, spaceAfter=2)
    subtitle_style = ParagraphStyle("DocSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=14, textColor=muted_text)
    badge_style = ParagraphStyle("Badge", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white)
    h2_style = ParagraphStyle("SectionH2", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=primary_color, spaceBefore=14, spaceAfter=6, keepWithNext=True)
    h3_style = ParagraphStyle("SectionH3", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=dark_slate, spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("BodyDark", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=dark_slate, spaceAfter=4)
    bullet_style = ParagraphStyle("Bullet", parent=body_style, leftIndent=14, firstLineIndent=0, bulletIndent=6, spaceAfter=3)
    table_cell = ParagraphStyle("Cell", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=dark_slate)
    table_header_style = ParagraphStyle("TableHeader", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white)
    disclaimer_style = ParagraphStyle("Disclaimer", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=8, leading=11, textColor=colors.HexColor("#475569"))
    caption_style = ParagraphStyle("Caption", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=muted_text)
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontName="Helvetica", fontSize=7, leading=9, textColor=muted_text)

    story: List[Any] = []

    report_type = str(report.get("report_type", "")).lower()
    type_label = "Palmistry Biometric Report" if report_type == "palmistry" else "Tarot Symbolic Report" if report_type == "tarot" else "Reading Report"
    confidence = report.get("confidence", {}) or {}
    conf_score = confidence.get("score", 85)
    conf_label = confidence.get("label", "High")

    # Cover / brand header
    brand_table = Table(
        [
            [Paragraph("<b>MYSTICLENS</b>  <font color='#B45309'>◆</font>  SPIRITUAL INTELLIGENCE", subtitle_style),
             Paragraph(f"<b>{_esc(type_label).upper()}</b>", ParagraphStyle("BrandRight", parent=subtitle_style, alignment=2, textColor=gold_color))],
        ],
        colWidths=[4.2 * inch, 2.8 * inch],
    )
    brand_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(brand_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(_esc(report.get("title", "Reading Report")), title_style))
    story.append(Spacer(1, 2))

    meta_line = (
        f"<b>Prepared for:</b> {_esc(report.get('user_name', 'Seeker'))} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Date:</b> {_esc(report.get('created_at', ''))} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Confidence:</b> {_esc(conf_score)}% ({_esc(conf_label)})"
    )
    story.append(Paragraph(meta_line, subtitle_style))
    story.append(Spacer(1, 4))

    # Key facts strip: reading id / report id / status / review
    facts = [
        [Paragraph("<b>Reading ID</b>", caption_style), Paragraph(f"<font size=7>{_esc(str(report.get('reading_id', ''))[:36])}</font>", caption_style),
         Paragraph("<b>Status</b>", caption_style), Paragraph(_esc(report.get("reading_status", "completed") or "completed"), caption_style)],
        [Paragraph("<b>Report ID</b>", caption_style), Paragraph(f"<font size=7>{_esc(str(report.get('report_id', ''))[:36])}</font>", caption_style),
         Paragraph("<b>Review</b>", caption_style), Paragraph("Reviewed ✓" if report.get("reviewed") else "Awaiting review", caption_style)],
    ]
    facts_table = Table(facts, colWidths=[0.9 * inch, 2.5 * inch, 0.8 * inch, 1.8 * inch])
    facts_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("BOX", (0, 0), (-1, -1), 0.5, border_grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, border_grey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(facts_table)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=gold_color, spaceBefore=2, spaceAfter=8))

    # Summary
    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Paragraph(_esc(report.get("summary", "")), body_style))
    if report.get("question"):
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Sacred inquiry:</b> <i>“{_esc(report.get('question'))}”</i>", body_style))
    story.append(Spacer(1, 6))

    def styled_table(data, widths, header_bg=primary_color) -> Table:
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
            ("GRID", (0, 0), (-1, -1), 0.5, border_grey),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    def cell(text: str) -> Paragraph:
        return Paragraph(text, table_cell)

    def head(text: str) -> Paragraph:
        return Paragraph(f"<b>{html.escape(text, quote=False)}</b>", table_header_style)

    if report_type == "palmistry":
        palm = report.get("palm_features", {}) or {}
        story.append(Paragraph("Elemental Biometric Profile", h2_style))
        story.append(Paragraph(
            f"<b>Hand Element:</b> {_esc(palm.get('element', 'Earth'))} Hand &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Detected hand:</b> {_esc(palm.get('hand_detected', 'Right'))} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Landmarks:</b> {_esc(palm.get('landmarks_count', 21))}",
            body_style,
        ))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<i>{_esc(palm.get('shape_description', ''))}</i>", body_style))
        if palm.get("traits"):
            story.append(Paragraph(f"<b>Hand traits:</b> {_join(palm.get('traits'))}", body_style))
        # Feature metrics table
        feat_rows = [
            [head("Metric"), head("Value"), head("Metric"), head("Value")],
            [cell("<b>Palm length ÷ width</b>"), cell(_esc(palm.get("palm_length_to_width", "—"))),
             cell("<b>Finger ÷ palm ratio</b>"), cell(_esc(palm.get("finger_to_palm_ratio", "—")))],
            [cell("<b>Palm width</b>"), cell(_esc(palm.get("palm_width", "—"))),
             cell("<b>Palm height</b>"), cell(_esc(palm.get("palm_height", "—")))],
            [cell("<b>Handedness confidence</b>"), cell(_esc(palm.get("handedness_confidence", "—"))),
             cell("<b>Palmar view</b>"), cell("Yes — palmar" if palm.get("is_palmar", True) else "Dorsal (lower line clarity expected)")],
        ]
        story.append(Spacer(1, 6))
        story.append(styled_table(feat_rows, [1.7 * inch, 1.8 * inch, 1.7 * inch, 1.8 * inch]))
        story.append(Spacer(1, 4))

        finger = report.get("finger_structure", {}) or {}
        if any([finger.get("digit_ratio_2d_4d"), finger.get("thumb_angle_degrees"), finger.get("digit_ratio_interpretation"), finger.get("pinky_trait")]):
            story.append(Paragraph("Finger Structure & Digit Ratios", h3_style))
            story.append(Paragraph(
                f"<b>2D:4D digit ratio:</b> {_esc(finger.get('digit_ratio_2d_4d', '—'))} — {_esc(finger.get('digit_ratio_interpretation', ''))}<br/>"
                f"<b>Thumb:</b> {_esc(finger.get('thumb_angle_degrees', '—'))}° ({_esc(finger.get('thumb_flexibility', '—'))}) &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<b>Little finger:</b> {_esc(finger.get('pinky_trait', '—'))}",
                body_style,
            ))

        lines = report.get("lines", []) or []
        story.append(Paragraph(f"Primary Palm Lines Analysis ({len(lines)} lines)", h2_style))
        if lines:
            lines_data = [[head("Line"), head("Form"), head("Continuity"), head("Conf."), head("Interpretation")]]
            for line in lines:
                detected = line.get("detected", True)
                status = "" if detected else "<br/><i>(not clearly detected)</i>"
                form = f"{_esc(line.get('length', '—'))} · {_esc(line.get('clarity', '—'))}<br/>{_esc(line.get('curve', ''))}"
                lines_data.append([
                    cell(f"<b>{_esc(line.get('name', ''))}</b>{status}"),
                    cell(form),
                    cell(_esc(line.get("continuity", "—"))),
                    cell(_pct(line.get("confidence", 0))),
                    cell(_esc(line.get("interpretation", ""))),
                ])
            story.append(styled_table(lines_data, [1.15 * inch, 1.25 * inch, 1.0 * inch, 0.65 * inch, 2.95 * inch]))
            story.append(Spacer(1, 2))
            story.append(Paragraph("Continuity describes how steadily each line's energy is traced; faint or fragmented lines are reported honestly rather than guessed.", caption_style))
        else:
            story.append(Paragraph("No individual line traces were stored for this reading — the summary above carries the full biometric assessment.", body_style))
        story.append(Spacer(1, 6))

        mounts = report.get("mounts", []) or []
        story.append(Paragraph(f"Planetary Mounts Prominence ({len(mounts)} mounts)", h2_style))
        if mounts:
            mounts_data = [[head("Mount"), head("Prominence"), head("Score"), head("Archetypal meaning")]]
            for mount in mounts:
                extra = ""
                if mount.get("planetary_ruler") or mount.get("element"):
                    extra = f"<br/><font size=7 color='#64748B'>{_esc(mount.get('planetary_ruler', ''))}{', ' if mount.get('planetary_ruler') and mount.get('element') else ''}{_esc(mount.get('element', ''))}</font>"
                attrs = mount.get("core_attributes") or []
                attr_line = f"<br/><font size=7 color='#64748B'>{_join(attrs)}</font>" if attrs else ""
                mounts_data.append([
                    cell(f"<b>{_esc(mount.get('name', ''))}</b>{extra}"),
                    cell(_esc(mount.get("prominence", "Normal"))),
                    cell(_pct(mount.get("score", 50))),
                    cell(f"{_esc(mount.get('meaning', ''))}{attr_line}"),
                ])
            story.append(styled_table(mounts_data, [1.5 * inch, 1.0 * inch, 0.7 * inch, 3.8 * inch]))
        else:
            story.append(Paragraph("No mount prominence data was stored for this reading.", body_style))
        story.append(Spacer(1, 6))

    else:
        spread = report.get("spread_details", {}) or {}
        story.append(Paragraph("Spread & Inquiry Context", h2_style))
        story.append(Paragraph(
            f"<b>Inquiry:</b> <i>“{_esc(report.get('question', 'General Guidance'))}”</i><br/>"
            f"<b>Spread:</b> {_esc(spread.get('spread_name', 'Spread'))} ({_esc(spread.get('total_cards', 0))} cards) &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Deck:</b> {_esc(spread.get('deck_id', 'rider-waite-smith'))}"
            + (f" &nbsp;&nbsp;|&nbsp;&nbsp; <b>Focus:</b> {_esc(report.get('domain_focus'))}" if report.get("domain_focus") else ""),
            body_style,
        ))
        story.append(Spacer(1, 6))

        cards = report.get("cards", []) or []
        story.append(Paragraph(f"Cards Drawn & Archetypal Interpretations ({len(cards)} cards)", h2_style))
        if cards:
            cards_data = [[head("#"), head("Position"), head("Card"), head("Orient."), head("Core symbolic interpretation")]]
            for c in cards:
                keywords = c.get("keywords") or []
                kw_line = f"<br/><font size=7 color='#64748B'>{_join(keywords[:5])}</font>" if keywords else ""
                arcana = f"<br/><font size=7 color='#64748B'>{_esc(c.get('arcana', ''))}{(' · ' + _esc(c.get('suit'))) if c.get('suit') and c.get('suit') != 'None' else ''}</font>"
                cards_data.append([
                    cell(_esc(c.get("index", 1))),
                    cell(f"<b>{_esc(c.get('position_name', ''))}</b><br/><font size=7 color='#64748B'>{_esc(c.get('position_meaning', ''))}</font>"),
                    cell(f"<b>{_esc(c.get('name', ''))}</b>{arcana}{kw_line}"),
                    cell(_esc(c.get("orientation", "Upright"))),
                    cell(_esc(c.get("interpretation", ""))),
                ])
            story.append(styled_table(cards_data, [0.35 * inch, 1.55 * inch, 1.7 * inch, 0.8 * inch, 2.6 * inch]))
            story.append(Spacer(1, 6))

            # Domain guidance per card (love / career / spiritual)
            guided = [c for c in cards if c.get("domain_guidance")]
            if guided:
                story.append(Paragraph("Domain Guidance by Card", h3_style))
                for c in guided:
                    story.append(Paragraph(f"<b>{_esc(c.get('name', ''))}</b> — {_esc(c.get('position_name', ''))}", body_style))
                    for g in c.get("domain_guidance", [])[:3]:
                        label = g.get("label") or g.get("domain") or "Guidance"
                        story.append(Paragraph(f"<b>{_esc(label)}:</b> {_esc(g.get('text', ''))}", bullet_style, bulletText="•"))
                story.append(Spacer(1, 4))

            # Fortune & shadow/light insights
            for c in cards:
                extras: List[str] = []
                if c.get("fortune_telling"):
                    extras.append(f"<b>Traditional note:</b> {_join((c.get('fortune_telling') or [])[:2])}")
                if c.get("expanded_meanings"):
                    orientation = "Shadow" if str(c.get("orientation", "")).lower() == "reversed" else "Light"
                    extras.append(f"<b>{orientation} insights:</b> {_join((c.get('expanded_meanings') or [])[:3])}")
                if extras:
                    story.append(Paragraph(f"<b>{_esc(c.get('name', ''))}</b> — {' '.join(extras)}", body_style))
            story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("No cards were stored for this reading.", body_style))

        synthesis = report.get("synthesis", {}) or {}
        story.append(Paragraph("Spread Archetypal Synthesis", h2_style))
        synth_line = (
            f"<b>Dominant element:</b> {_esc(synthesis.get('elemental_dominance', 'Balanced'))} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Reversals:</b> {_esc(synthesis.get('reversals_count', 0))}"
        )
        story.append(Paragraph(synth_line, body_style))
        arc_dist = synthesis.get("arcana_distribution", {}) or {}
        if isinstance(arc_dist, dict) and arc_dist:
            story.append(Paragraph(f"<b>Arcana balance:</b> {_esc(arc_dist.get('major', 0))} major · {_esc(arc_dist.get('minor', 0))} minor", body_style))
        for key, label in (("arcana_narrative", "Arcana"), ("elemental_narrative", "Elements"), ("reversal_narrative", "Reversals"), ("numerology_narrative", "Numerology")):
            if synthesis.get(key):
                story.append(Paragraph(f"<b>{label}:</b> {_esc(synthesis.get(key))}", body_style))
        narrative = report.get("narrative", {}) or {}
        if narrative.get("opening"):
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<i>{_esc(narrative.get('opening'))}</i>", body_style))
        if narrative.get("theme"):
            story.append(Paragraph(f"<b>Theme:</b> {_esc(narrative.get('theme', 'Insight'))}", body_style))
        if narrative.get("body"):
            body_lines = narrative.get("body") if isinstance(narrative.get("body"), list) else [narrative.get("body")]
            items = [ListItem(Paragraph(_esc(line), body_style), leftIndent=14) for line in body_lines if str(line).strip()]
            if items:
                story.append(ListFlowable(items, bulletType="bullet", leftIndent=14, bulletFontSize=7))
        if narrative.get("full_text") and narrative.get("full_text") != narrative.get("summary"):
            story.append(Paragraph(_esc(narrative.get("full_text", "")), body_style))
        if narrative.get("closing"):
            story.append(Paragraph(f"<i>{_esc(narrative.get('closing'))}</i>", body_style))
        story.append(Spacer(1, 6))

    # AI interpretation (opt-in layer, shown when present)
    ai = report.get("ai_interpretation") or {}
    if isinstance(ai, dict) and (ai.get("summary") or ai.get("narrative") or ai.get("interpretation")):
        story.append(Paragraph("AI Reflective Interpretation", h2_style))
        if ai.get("summary"):
            story.append(Paragraph(_esc(ai.get("summary")), body_style))
        long_text = ai.get("narrative") or ai.get("interpretation") or ""
        if long_text:
            story.append(Paragraph(_esc(long_text), body_style))
        story.append(Spacer(1, 4))

    # Seeker notes (personal journal excerpt, when present)
    if report.get("reading_notes"):
        story.append(Paragraph("Seeker's Journal Notes", h3_style))
        story.append(Paragraph(f"<i>“{_esc(report.get('reading_notes'))}”</i>", body_style))
        story.append(Spacer(1, 4))

    # Actionable guidance
    actions = report.get("actionable_guidance", []) or []
    if actions:
        story.append(Paragraph("Reflective Guidance & Action Steps", h2_style))
        numbered = [ListItem(Paragraph(_esc(item), body_style), leftIndent=16) for item in actions]
        story.append(ListFlowable(numbered, bulletType="1", leftIndent=16))
        story.append(Spacer(1, 8))

    # Ethical disclaimer (§49.19)
    disclaimer_table = Table(
        [[Paragraph(f"<b>Safety & Ethics Notice:</b> {_esc(report.get('disclaimer', ''))}", disclaimer_style)]],
        colWidths=[7.0 * inch],
    )
    disclaimer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.5, border_grey),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.append(KeepTogether(disclaimer_table))

    # Footer metadata (Rule 11)
    engine_meta = report.get("engine_metadata", {}) or {}
    footer_text = (
        f"Generated by {_esc(engine_meta.get('engine', 'MysticLensEngine'))} v{_esc(engine_meta.get('version', '1.0'))} "
        f"at {_esc(engine_meta.get('timestamp_utc', ''))}. Report {_esc(str(report.get('report_id', ''))[:8])} · Reading {_esc(str(report.get('reading_id', ''))[:8])}."
    )
    story.append(Spacer(1, 8))
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
