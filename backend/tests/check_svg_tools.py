try:
    import cairosvg
    print("cairosvg available")
except Exception as e:
    print("cairosvg not available:", e)

try:
    from svglib.svglib import svg2rlg
    print("svglib available")
except Exception as e:
    print("svglib not available:", e)
