# -*- coding: utf-8 -*-
"""
מרכיב את הדשבורד מהתבנית + הנתונים + הלוגו.

שני ניתובים נפרדים, משני קהלים שונים (ראו CLAUDE.md „שני ניתובי הפרסום”):

  dashboard/index.html          — הגרסה המלאה, עם „תובנות” — לשימוש פנימי/מומחה בלבד
  dashboard/artifact.html       — אותו תוכן ללא עטיפת <html>/<head>/<body>, לפרסום כ-Artifact
  dashboard/index_public.html   — גרסת ה-BI הציבורית: אותם נתונים וגרפים, בלי כפתורי
                                   „תובנות” ובלי הגישה אליהן (עוד דורשות מעבר מומחה)
  dashboard/artifact_public.html — אותו תוכן ציבורי, לפרסום כ-Artifact נפרד

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


def render(tpl, data, logo, public):
    """מזריק נתונים + לוגו לתבנית. public=True מפיק את גרסת ה-BI הציבורית —
    אותם נתונים וגרפים, בלי „insights” ובלי כפתורי הגישה אליהן (ראו CLAUDE.md)."""
    data = dict(data, public=public)
    if public:
        data["insights"] = []
    page = tpl.replace('"__DATA__"', json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    return page.replace("__LOGO__", logo)


def main():
    with open(os.path.join(HERE, "template.html"), encoding="utf-8") as f:
        tpl = f.read()
    with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(HERE, "btl.json"), encoding="utf-8") as f:
        data["btl2"] = json.load(f)      # חלק ב׳ — ראו build_btl.py

    logo = logo_data_uri()
    full = render(tpl, data, logo, public=False)
    public = render(tpl, data, logo, public=True)

    outputs = (
        ("index.html", HEAD + full + FOOT),
        ("artifact.html", full),
        ("index_public.html", HEAD + public + FOOT),
        ("artifact_public.html", public),
    )
    for name, body in outputs:
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        print(f"נכתב {p}  ({os.path.getsize(p):,} bytes)")


if __name__ == "__main__":
    main()
