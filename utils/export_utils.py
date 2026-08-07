"""Download helpers for records created in BizForge."""

import csv
import io
import re
from datetime import datetime
from html import escape

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _safe_filename(filename):
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
    return safe or "bizforge_export"


def copy_to_clipboard(text):
    """Show selectable text; browser clipboard access is not reliable from Streamlit."""
    st.code(text, language=None)


def export_to_csv(content, filename="export"):
    csv_file = io.StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(["Content"])
    writer.writerow([content])
    st.download_button(
        label="Download CSV",
        data=csv_file.getvalue().encode("utf-8"),
        file_name=f"{_safe_filename(filename)}_{datetime.now():%Y%m%d_%H%M%S}.csv",
        mime="text/csv",
    )


def build_pdf(content, title="Document"):
    """Create a real PDF in memory without writing a temporary customer file."""
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=title,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(title), styles["Title"]), Spacer(1, 0.35 * cm)]
    for line in content.splitlines():
        story.append(Paragraph(escape(line) or "&nbsp;", styles["BodyText"]))
        story.append(Spacer(1, 0.08 * cm))
    document.build(story)
    return buffer.getvalue()


def export_to_pdf(content, title="Document", filename="export"):
    st.download_button(
        label="Download PDF",
        data=build_pdf(content, title),
        file_name=f"{_safe_filename(filename)}_{datetime.now():%Y%m%d_%H%M%S}.pdf",
        mime="application/pdf",
    )


def export_section(content, title="Document", filename="export"):
    st.markdown("### Export")
    col1, col2, col3 = st.columns(3)
    with col1:
        copy_to_clipboard(content)
    with col2:
        export_to_csv(content, filename)
    with col3:
        export_to_pdf(content, title, filename)
