import inspect
from reportlab.graphics import renderPDF

lines, start = inspect.getsourcelines(renderPDF._PDFRenderer.drawRect)
print("".join(lines[:30]))
