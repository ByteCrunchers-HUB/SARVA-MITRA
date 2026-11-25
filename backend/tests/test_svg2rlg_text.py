import pypdf
from svglib.svglib import svg2rlg
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

svg_path = "/home/vijay/git/SARVA-MITRA/frontend/assets/logo.svg"
drawing = svg2rlg(svg_path)
scale = 0.3
drawing.width = drawing.width * scale
drawing.height = drawing.height * scale
drawing.scale(scale, scale)

buf = io.BytesIO()
doc = SimpleDocTemplate(buf)
styles = getSampleStyleSheet()
story = [drawing, Paragraph("Hello Sarva Mitra", styles["Normal"])]
doc.build(story)

reader = pypdf.PdfReader(io.BytesIO(buf.getvalue()))
print("Extracted text from page 0:")
print(repr(reader.pages[0].extract_text()))
