from PIL import Image
from pathlib import Path

assets_dir = Path("/home/vijay/git/SARVA-MITRA/frontend/assets")
for f in assets_dir.iterdir():
    if f.suffix in [".png", ".jpg", ".jpeg", ".svg"]:
        try:
            im = Image.open(f)
            print(f.name, im.size, im.format, im.mode)
        except Exception as e:
            print(f.name, "SVG or not PIL readable", e)
