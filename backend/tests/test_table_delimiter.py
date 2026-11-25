import re

pattern = re.compile(r"^\|?[\s\-:]+(\|[\s\-:]+)+\|?$")
test_lines = [
    "|---|---|---|",
    "|:---|:---:|---:|",
    "| :--- | :---: | ---: |",
    "| - | - | - |",
    "| --- | --- |",
    "|---|",
    "---|---|---",
    ":---|:---",
]

for l in test_lines:
    m = bool(pattern.match(l))
    print(f"{l!r:30} -> {m}")
