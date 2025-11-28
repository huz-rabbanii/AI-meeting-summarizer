"""
PDF export — generates a clean PDF report from a meeting's results.
Uses fpdf2 (pip install fpdf2) — no system dependencies required.
"""

import os
from fpdf import FPDF
from datetime import datetime


def _fmt_ms(ms: int) -> str:
    """Convert milliseconds to MM:SS string."""
    s = ms // 1000
    return f"{s // 60:02d}:{s % 60:02d}"


def export_pdf(meeting_data: dict) -> bytes:
    """
    meeting_data keys: title, created_at, duration_seconds,
                       transcript, summary, action_items, speakers, chapters, keywords
    Returns raw PDF bytes.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Header ────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "Meeting Summary Report", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    title = meeting_data.get("title", "Untitled Meeting")
    created = meeting_data.get("created_at", "")
    if hasattr(created, "strftime"):
        created = created.strftime("%B %d, %Y %H:%M UTC")
    dur = meeting_data.get("duration_seconds") or 0
    dur_str = f"{dur // 60}m {dur % 60}s" if dur else "—"

    pdf.cell(0, 7, f"Title:    {title}",   ln=True)
    pdf.cell(0, 7, f"Date:     {created}", ln=True)
    pdf.cell(0, 7, f"Duration: {dur_str}", ln=True)
    pdf.ln(4)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    def section_heading(text: str):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, text, ln=True)
        pdf.ln(2)

    def body_text(text: str, color=(80, 80, 80)):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, 6, text)
        pdf.ln(2)

    # ── Summary ───────────────────────────────────────────────────
    if meeting_data.get("summary"):
        section_heading("Summary")
        body_text(meeting_data["summary"])
        pdf.ln(2)

    # ── Action Items ──────────────────────────────────────────────
    action_items = meeting_data.get("action_items") or []
    if action_items:
        section_heading("Action Items")
        for i, item in enumerate(action_items, 1):
            body_text(f"{i}. {item}")
        pdf.ln(2)

    # ── Chapters ──────────────────────────────────────────────────
    chapters = meeting_data.get("chapters") or []
    if chapters:
        section_heading("Topics / Chapters")
        for ch in chapters:
            start_str = _fmt_ms(ch.get("start", 0)) if ch.get("start") else ""
            heading = ch.get("title", "")
            if start_str:
                heading = f"[{start_str}] {heading}"
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 6, heading, ln=True)
            if ch.get("summary"):
                body_text(ch["summary"])
        pdf.ln(2)

    # ── Keywords ─────────────────────────────────────────────────
    keywords = meeting_data.get("keywords") or []
    if keywords:
        section_heading("Key Terms")
        body_text(", ".join(keywords))
        pdf.ln(2)

    # ── Speaker Breakdown ─────────────────────────────────────────
    speakers = meeting_data.get("speakers") or []
    if speakers:
        pdf.add_page()
        section_heading("Speaker Transcript")
        current_speaker = None
        for seg in speakers:
            spk = seg.get("speaker", "Speaker ?")
            if spk != current_speaker:
                current_speaker = spk
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(40, 80, 160)
                start = _fmt_ms(seg.get("start", 0))
                pdf.cell(0, 7, f"{spk}  [{start}]", ln=True)
            body_text(seg.get("text", ""))

    # ── Full Transcript ────────────────────────────────────────────
    transcript = meeting_data.get("transcript") or ""
    if transcript and not speakers:
        pdf.add_page()
        section_heading("Full Transcript")
        # Chunk to avoid FPDF multi_cell overflow on very long texts
        chunk_size = 1500
        for i in range(0, len(transcript), chunk_size):
            body_text(transcript[i:i + chunk_size])

    return bytes(pdf.output())
