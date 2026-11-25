from svglib.svglib import svg2rlg

drawing = svg2rlg("/home/vijay/git/SARVA-MITRA/frontend/assets/logo-report.svg")
# Find Rect
for item in drawing.contents[0].contents[0].contents:
    if item.__class__.__name__ == "Rect":
        print("Rect attributes:", vars(item))
