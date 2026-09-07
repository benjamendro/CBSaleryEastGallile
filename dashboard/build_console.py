# -*- coding: utf-8 -*-
"""
מייצר את **הגרסה הציבורית של קונסולת ה-BI** מתוך המקור הפנימי.

קונסולת ה-BI היא „מסך אחד” — טאבים, סרגל פילטרים, שורת KPI וגריד פאנלים —
להבדיל מהדו״ח הנרטיבי הארוך שמיוצר ב-build.py. זהו הממשק שמתפרסם החוצה.

    dashboard/console_source.html  →  dashboard/console_public.html

שלוש פעולות, וכל אחת מהן נדרשת כדי שהקובץ יהיה ראוי לפרסום:

1. **ריקון `DATA.insights`.** המקור נושא 19 תובנות עם גוף הטקסט המלא. הקונסולה
   אינה מציגה אותן בשום מקום בממשק — הן יושבות שם רק כדי שמצב העריכה יוכל
   לייצא אותן בחזרה ל-content.json — אבל הן קריאות ב-view-source, וזה פרסום
   לכל דבר. הן דורשות מעבר מומחה לפני שיֵצאו החוצה.
2. **הסרת הקישור „הדו״ח המלא והתובנות ←”** שבכותרת. הוא מצביע על Artifact
   פנימי; מבחוץ הוא גם שבור וגם מכריז על קיומן של התובנות.
3. **הסרת מצב העריכה.** בקובץ המפורסם אין „עריכת טקסט”: לא הכפתור שבכותרת, לא סרגל
   העריכה התחתון, ולא הקריאה ל-`wireEditing()`. העריכה היא כלי עבודה פנימי — מי שצופה
   בקישור הציבורי אינו אמור לשנות את הטקסט, ואינו אמור לראות פקד שמזמין לכך.
   (`window.__reapplyEdit` כבר מוגן בקוד המקור, ולכן ביטול החיווט אינו שובר את הציור מחדש.)
4. **סימון הניתוב** — `const PUBLIC = true;` — כדי שהקובץ יצהיר על עצמו.

הרצה: python3 dashboard/build_console.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "console_source.html")
TARGET = os.path.join(HERE, "console_public.html")

REPORT_LINK = re.compile(
    r'\s*<a\b[^>]*id="reportLink"[^>]*>.*?</a>', re.S)
EDIT_TOGGLE = re.compile(
    r'\s*<button\b[^>]*id="editToggle"[^>]*>.*?</button>', re.S)
EDIT_BAR = re.compile(
    r'\s*<div\b[^>]*id="editbar"[^>]*>.*?</div>', re.S)
EDIT_CALL = re.compile(r'\bwireEditing\(\);')


def block_span(html, start):
    """מאתר גוש `{...}` מאוזן החל מהתו `{` הראשון אחרי start, בדילוג על מחרוזות."""
    brace = html.find("{", start)
    depth, quote, escaped = 0, "", False
    for index in range(brace, len(html)):
        char = html[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in "\"'`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return brace, index + 1
    sys.exit("גוש הקוד אינו מאוזן")


def data_span(html):
    """מאתר את אובייקט ה-DATA המוזרק, בסריקת סוגריים שמכבדת מחרוזות."""
    start = html.find("const DATA")
    if start == -1:
        sys.exit("לא נמצא אובייקט DATA בקובץ המקור")
    brace = html.find("{", start)
    depth, in_string, escaped = 0, False, False
    for index in range(brace, len(html)):
        char = html[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return brace, index + 1
    sys.exit("אובייקט ה-DATA אינו מאוזן")


def main():
    if not os.path.exists(SOURCE):
        sys.exit(f"חסר {SOURCE} — המקור הפנימי של הקונסולה")
    with open(SOURCE, encoding="utf-8") as f:
        html = f.read()

    # 1 — ריקון התובנות מתוך המטען המוטמע
    start, end = data_span(html)
    data = json.loads(html[start:end])
    dropped = len(data.get("insights") or [])
    data["insights"] = []
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = html[:start] + payload + html[end:]

    # 2 — הסרת הקישור לדו״ח המלא ולתובנות
    html, links = REPORT_LINK.subn("", html)

    # 3 — הסרת מצב העריכה: הכפתור, הסרגל, החיווט, והפונקציה כולה
    html, toggles = EDIT_TOGGLE.subn("", html)
    html, bars = EDIT_BAR.subn("", html)
    html, calls = EDIT_CALL.subn("", html)
    fn = html.find("function wireEditing")
    if fn == -1:
        sys.exit("wireEditing לא נמצאה — המקור השתנה")
    open_brace, close_brace = block_span(html, fn)
    html = html[:fn] + html[close_brace:]

    # 4 — הצהרת הניתוב
    html = html.replace('<script>\n"use strict";',
                        '<script>\n"use strict";\nconst PUBLIC = true;', 1)

    # שערי בטיחות — נכשלים ברעש ולא בשקט
    if '"insights":[]' not in html:
        sys.exit("התובנות לא רוקנו — הפלט אינו ראוי לפרסום")
    if "claude.ai/code/artifact" in html:
        sys.exit("נותר קישור ל-Artifact פנימי — הפלט אינו ראוי לפרסום")
    if (toggles, bars, calls) != (1, 1, 1):
        sys.exit(f"מצב העריכה לא הוסר במלואו "
                 f"(כפתור={toggles}, סרגל={bars}, חיווט={calls}) — המקור השתנה")
    for leftover in ('id="editToggle"', 'id="editbar"', "wireEditing()"):
        if leftover in html:
            sys.exit(f"נותר {leftover} — מצב העריכה עדיין נגיש")
    if "const PUBLIC = true;" not in html:
        sys.exit("הצהרת הניתוב לא נכתבה")

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"נכתב {TARGET}  ({os.path.getsize(TARGET):,} bytes)")
    print(f"  הוסרו {dropped} תובנות · {links} קישורים לדו״ח הפנימי · מצב העריכה הוסר")


if __name__ == "__main__":
    main()
