# -*- coding: utf-8 -*-
"""
מרכיב את הדשבורד מהתבנית + הנתונים + הלוגו.

פלט:
  dashboard/index.html     — קובץ HTML עצמאי אחד (נפתח בכל דפדפן, ללא תלות ברשת)
  dashboard/artifact.html  — אותו תוכן ללא עטיפת <html>/<head>/<body>, לפרסום כ-Artifact

הרצה: python3 dashboard/build_data.py && python3 dashboard/build.py
"""
import base64, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGO = os.path.join(ROOT, "design", "assets", "logo.jpg")

HEAD = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
"""
FOOT = "\n</body>\n</html>\n"


def logo_data_uri():
    """מקטין את הלוגו ומחזיר אותו כ-data URI, כדי שהקובץ יהיה עצמאי לחלוטין."""
    from PIL import Image
    im = Image.open(LOGO).convert("RGB")
    h = 140
    w = round(im.size[0] * h / im.size[1])
    buf = io.BytesIO()
    im.resize((w, h), Image.LANCZOS).save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main():
    with open(os.path.join(HERE, "template.html"), encoding="utf-8") as f:
        tpl = f.read()
    with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(HERE, "btl.json"), encoding="utf-8") as f:
        data["btl2"] = json.load(f)      # חלק ב׳ — ראו build_btl.py

    page = tpl.replace('"__DATA__"', json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    page = page.replace("__LOGO__", logo_data_uri())

    for name, body in (("index.html", HEAD + page + FOOT), ("artifact.html", page)):
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        print(f"נכתב {p}  ({os.path.getsize(p):,} bytes)")


if __name__ == "__main__":
    main()
