from pathlib import Path
from svglib.svglib import svg2rlg
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

def test_svg():
    svg_path = Path("frontend/assets/logo.svg")
    assert svg_path.exists(), "SVG not found"
    drawing = svg2rlg(str(svg_path))
    print(f"Loaded SVG successfully: original size {drawing.width}x{drawing.height}")
    
    # Scale to width 180 pt
    target_width = 180.0
    factor = target_width / drawing.width
    drawing.width = target_width
    drawing.height = drawing.height * factor
    drawing.scale(factor, factor)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = [drawing]
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    print(f"Built PDF with SVG drawing: {len(pdf_bytes)} bytes")
    assert len(pdf_bytes) > 1000

if __name__ == "__main__":
    test_svg()
