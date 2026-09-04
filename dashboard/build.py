# -*- coding: utf-8 -*-
"""
מרכיב את הדשבורד מהתבנית + הנתונים + הלוגו.

שני פלטים, מאותם נתונים:

  הדו"ח (נרטיבי, עם התובנות)      template.html          → index.html   · artifact.html
  קונסולת BI (גרפים בלבד)          console-template.html  → console.html · console-artifact.html

הרצה: python3 dashboard/build_data.py && python3 dashboard/build.py
"""
import base64, io, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGO = os.path.join(ROOT, "design", "assets", "logo.jpg")

# הקישורים ההדדיים בין שני הפלטים. בקבצים המקומיים הם יחסיים; בגרסאות
# ה-Artifact הם חייבים להיות מוחלטים, כי שני ה-Artifacts הם דפים נפרדים.
ART_REPORT  = "https://claude.ai/code/artifact/fe33a2c0-c0ec-4fcf-9c2b-7affa22525e5"
ART_CONSOLE = "https://claude.ai/code/artifact/17d58cf2-00a8-43e0-9d64-3bb58d2d34eb"

HEAD = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
"""
FOOT = "\n</body>\n</html>\n"



def part_c_engine():
    """מנוע הגרפים של חלק ג׳, מתוך analysis/src/charts.js — מקור אמת אחד.

    הקובץ נכתב כדף עצמאי ולכן נדרשות ארבע התאמות: הסרת עטיפת ה-<script>,
    חיבור ל-DATA.rep במקום ל-window.__D__, ה-tooltip של חלק ג׳ במקום זה של
    דף הניתוח, והסרת ההרצה האוטומטית — הציור מופעל מ-renderPartC אחרי
    שה-DOM נבנה. הגופן מותאם לגופן הדשבורד.
    """
    src = os.path.join(ROOT, "analysis", "src", "charts.js")
    with open(src, encoding="utf-8") as f:
        js = f.read()
    js = js.replace("<script>", "", 1)
    js = re.sub(r"</script>\s*$", "", js.strip())
    js = js.replace("const D = window.__D__;", "const D = DATA.rep;")
    js = js.replace("const tip=document.getElementById('tip');",
                    "const tip=document.getElementById('ctip');")
    js = js.replace("'Heebo,sans-serif'", "'Assistant,system-ui,sans-serif'")
    js = re.sub(r"\ndrawAll\(\);.*$", "", js, flags=re.S)
    for must in ("function drawAll", "DATA.rep", "'ctip'"):
        if must not in js:
            raise SystemExit(f"charts.js: ההתאמה נכשלה — חסר {must!r}")
    if "window.__D__" in js:
        raise SystemExit("charts.js: נותרה הפניה ל-window.__D__")
    return js


def logo_data_uri():
    """מקטין את הלוגו ומחזיר אותו כ-data URI, כדי שהקובץ יהיה עצמאי לחלוטין."""
    from PIL import Image
    im = Image.open(LOGO).convert("RGB")
    h = 140
    w = round(im.size[0] * h / im.size[1])
    buf = io.BytesIO()
    im.resize((w, h), Image.LANCZOS).save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build(template, local_name, artifact_name, data_json, logo, links, charts=""):
    """מרכיב תבנית אחת לשני פלטים: קובץ עצמאי, וגרסת Artifact בלי עטיפה."""
    with open(os.path.join(HERE, template), encoding="utf-8") as f:
        tpl = f.read()
    page = (tpl.replace('"__DATA__"', data_json).replace("__LOGO__", logo)
               .replace('"__PARTC_CHARTS__"', charts))
    for name, wrap, (rep, con) in (
            (local_name, True, links["local"]),
            (artifact_name, False, links["artifact"])):
        body = page.replace("__REPORT_URL__", rep).replace("__CONSOLE_URL__", con)
        out = (HEAD + body + FOOT) if wrap else body
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"נכתב {p}  ({os.path.getsize(p):,} bytes)")


def main():
    with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(HERE, "btl.json"), encoding="utf-8") as f:
        data["btl2"] = json.load(f)      # חלק ב׳ — ראו build_btl.py

    # חלק ג׳ — הניתוח המעמיק. מקור נפרד: קבצי ההכנסה המנהליים של הלמ"ס,
    # לא העיבוד המיוחד שמזין את חלק א׳. רמות השכר בשני הקבצים נבדלות
    # במקדם משתנה (1.09–1.25) ולכן לעולם אינן מוצגות על אותו ציר.
    rep = os.path.join(ROOT, "analysis", "output", "report_data.json")
    with open(rep, encoding="utf-8") as f:
        data["rep"] = json.load(f)

    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    # הקונסולה אינה מרנדרת את חלק ג׳, ולכן אינה נושאת את מטענו (כ-45KB).
    # בניגוד ל„insights”, המפתח „rep” אינו חלק ממחזור העריכה של content.json,
    # ולכן השמטתו כאן אינה יכולה לאבד תוכן שנערך.
    console_json = json.dumps({k: v for k, v in data.items() if k != "rep"},
                              ensure_ascii=False, separators=(",", ":"))
    logo = logo_data_uri()
    links = {"local": ("index.html", "console.html"),
             "artifact": (ART_REPORT, ART_CONSOLE)}

    build("template.html", "index.html", "artifact.html", data_json, logo, links,
          charts=part_c_engine())
    build("console-template.html", "console.html", "console-artifact.html",
          console_json, logo, links)


if __name__ == "__main__":
    main()
