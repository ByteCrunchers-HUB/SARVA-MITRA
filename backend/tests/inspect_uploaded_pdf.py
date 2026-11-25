import pypdf
from pathlib import Path

pdf_path = Path("/mnt/c/Users/Vijay Karthik/.gemini/antigravity/brain/a90e6c9e-b932-4c93-845f-744f5073ae79/.user_uploaded/media_1795520050696_6e055887.pdf")
if not pdf_path.exists():
    print(f"File not found: {pdf_path}")
else:
    reader = pypdf.PdfReader(str(pdf_path))
    print(f"Total Pages: {len(reader.pages)}")
    for i, p in enumerate(reader.pages):
        print(f"\n=== PAGE {i+1} ===")
        print(p.extract_text())
