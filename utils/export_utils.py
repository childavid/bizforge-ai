import streamlit as st
from datetime import datetime
import csv
import io


def copy_to_clipboard(text):
    """Copy text to clipboard"""
    st.code(text, language=None)
    st.button("📋 Copy to Clipboard", on_click=lambda: st.session_state.update(copied_text=text))


def export_to_csv(content, filename="export"):
    """Export content to CSV"""
    csv_file = io.StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(["Content"])
    writer.writerow([content])
    
    csv_bytes = csv_file.getvalue().encode('utf-8')
    st.download_button(
        label="📥 Download as CSV",
        data=csv_bytes,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def export_to_pdf(content, title="Document", filename="export"):
    """Export content to PDF (simplified as text download for now)"""
    # For a true PDF, we'd need reportlab or similar
    # For now, we'll export as a formatted text file that can be printed to PDF
    pdf_content = f"""
{title}
{'=' * len(title)}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{content}
"""
    
    st.download_button(
        label="📥 Download as PDF (Text)",
        data=pdf_content,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )


def export_section(content, title="Document", filename="export"):
    """Display export buttons for a content section"""
    st.markdown("### 📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Copy to Clipboard", key=f"copy_{filename}"):
            st.session_state[f"copied_{filename}"] = content
            st.success("✅ Copied to clipboard!")
    
    with col2:
        export_to_csv(content, filename)
    
    with col3:
        export_to_pdf(content, title, filename)
    
    st.divider()
