from svglib.svglib import svg2rlg
from reportlab.graphics.shapes import Group, Rect, Path, Circle, String
import sys

drawing = svg2rlg("/home/vijay/git/SARVA-MITRA/frontend/assets/logo-report.svg")
print("Drawing type:", type(drawing))

def inspect_node(node, indent=0):
    space = "  " * indent
    print(f"{space}{type(node).__name__}: {getattr(node, 'properties', {})}")
    if hasattr(node, 'contents'):
        for child in node.contents:
            inspect_node(child, indent + 1)

inspect_node(drawing)
