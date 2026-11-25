from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM
import os

svg_path = "/home/vijay/git/SARVA-MITRA/frontend/assets/logo.svg"
drawing = svg2rlg(svg_path)
print("Drawing:", drawing.width, drawing.height)
renderPM.drawToFile(drawing, "/home/vijay/git/SARVA-MITRA/frontend/assets/logo-full.png", fmt="PNG")
print("Saved logo-full.png, size:", os.path.getsize("/home/vijay/git/SARVA-MITRA/frontend/assets/logo-full.png"))
