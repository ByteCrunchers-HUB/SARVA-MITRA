from svglib.svglib import svg2rlg
from reportlab.platypus import SimpleDocTemplate, Table
from pathlib import Path
import io

svg_path = "/home/vijay/git/SARVA-MITRA/frontend/assets/logo.svg"
try:
    drawing = svg2rlg(svg_path)
    print("svg2rlg succeeded! drawing:", drawing.width, drawing.height)
except Exception as e:
    print("svg2rlg error:", e)
