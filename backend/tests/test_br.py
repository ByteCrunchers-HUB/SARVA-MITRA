from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()
try:
    p = Paragraph("Line 1<br>Line 2", styles["Normal"])
    print("Paragraph with <br> succeeded")
except Exception as e:
    print("Paragraph with <br> FAILED:", e)

try:
    p = Paragraph("Line 1<br/>Line 2", styles["Normal"])
    print("Paragraph with <br/> succeeded")
except Exception as e:
    print("Paragraph with <br/> FAILED:", e)
