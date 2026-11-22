import base64
from pathlib import Path

svg_path = Path("frontend/assets/logo.svg")
with open(svg_path, "rb") as f:
    data = f.read()
b64 = base64.b64encode(data).decode("utf-8")
print(f"SVG read successfully, length={len(data)}, b64_len={len(b64)}")
