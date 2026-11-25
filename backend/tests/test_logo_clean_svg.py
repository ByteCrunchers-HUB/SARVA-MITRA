import pypdf
from svglib.svglib import svg2rlg
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.styles import getSampleStyleSheet
import io

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 180" width="640" height="180">
  <g id="icon">
    <rect x="24" y="10" width="160" height="160" rx="36" ry="36" fill="#2E6B4F" />
    <path d="M 68 130 C 66 84, 98 50, 146 48 C 142 96, 114 128, 68 130 Z" fill="#FFFFFF" />
    <path d="M 66 132 Q 100 96, 132 64" fill="none" stroke="#2E6B4F" stroke-width="6.5" stroke-linecap="round" />
    <g fill="none" stroke="#CFA83E" stroke-width="5.5" stroke-linecap="round">
      <circle cx="142" cy="138" r="4.5" fill="#CFA83E" stroke="none" />
      <path d="M 142 122 A 16 16 0 0 1 158 138" />
      <path d="M 142 110 A 28 28 0 0 1 170 138" />
    </g>
  </g>
  <g id="wordmark">
    <text x="212" y="75" font-family="Helvetica, Arial, sans-serif" font-size="52" font-weight="bold" fill="#1E2823">Sarva Mitra</text>
    <text x="214" y="115" font-family="Helvetica, Arial, sans-serif" font-size="28" font-weight="bold" fill="#2E6B4F">UNIVERSAL FARM COMPANION</text>
    <text x="214" y="148" font-family="Helvetica, Arial, sans-serif" font-size="20" fill="#4A6352">One device. Any farm. Any language.</text>
  </g>
</svg>"""

with open("/tmp/logo_clean.svg", "w") as f:
    f.write(svg_content)

drawing = svg2rlg("/tmp/logo_clean.svg")
target_w = 200.0
factor = target_w / float(drawing.width)
drawing.width = target_w
drawing.height = float(drawing.height) * factor
drawing.scale(factor, factor)

buf = io.BytesIO()
doc = SimpleDocTemplate(buf)
doc.build([drawing])

reader = pypdf.PdfReader(io.BytesIO(buf.getvalue()))
text = reader.pages[0].extract_text()
print("Extracted text:")
print(repr(text))
print("Any null characters (\\x00)?", "\x00" in text)
