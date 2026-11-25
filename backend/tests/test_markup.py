import re
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def format_inline_markup(line: str) -> str:
    if not line:
        return ""
    line = re.sub(r"<br\s*/?>", "<br/>", line, flags=re.IGNORECASE)
    line = re.sub(r"&(?!([a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);)", "&amp;", line)
    line = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", line)
    line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
    line = re.sub(r"\*(.*?)\*", r"<i>\1</i>", line)
    line = re.sub(r"`(.*?)`", r"<font face='Courier'>\1</font>", line)

    parts = re.split(r"(</?[bi]>|<br/>|</?font[^>]*>)", line)
    escaped_parts = []
    for p in parts:
        if re.match(r"^</?[bi]>$|^<br/>$|^</?font[^>]*>$", p):
            escaped_parts.append(p)
        else:
            p = p.replace("<", "&lt;").replace(">", "&gt;")
            escaped_parts.append(p)
    return "".join(escaped_parts)

styles = getSampleStyleSheet()
test_cases = [
    "Test with <br> and <BR> tags",
    "Test **bold** and *italic* and `code`",
    "Test with raw <unknown> and > characters",
    "Test with & ampersand and &bull; entity",
    "Temperature < 28 & Humidity > 70%",
]

for tc in test_cases:
    formatted = format_inline_markup(tc)
    try:
        p = Paragraph(formatted, styles["Normal"])
        print("OK:", tc, "->", formatted)
    except Exception as e:
        print("FAIL:", tc, "->", formatted, "ERR:", e)
