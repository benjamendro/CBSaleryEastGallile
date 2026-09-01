# -*- coding: utf-8 -*-
"""לוחות הביטוח הלאומי → dashboard/btl.json  (חלק ב׳ של הדשבורד).

    export BTL_DIR=/path/to/relevant_tables
    python3 dashboard/build_btl.py

נכשל בכוונה אם: החלוקה א׳=ד׳+ז׳+ח׳ אינה מתלכדת · נמצאו פחות מ-13 יישובים או
פחות מ-4 מועצות אזוריות · רצועות ההתפלגות אינן סוכמות ל-100% · סדרת המגמה
מחושבת על בסיס רשויות משתנה.

כללי היסוד (ראו docs/dashboard-architecture.md):
  · „כלל העובדים” מחושב תמיד כ-ד׳+ז׳+ח׳ ולעולם לא נקרא מהלוח — עמודת 2019
    בלוח 3 מעורבבת בין שורות ב-49 יישובים.
  · שקלול קבוצות של אנשים נעשה לפי מספר האנשים.
  · שום ערך כאן לא נועד להיות מוצג לצד ערך של הלמ"ס על אותו ציר.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from btl_read import read, find, geo_of_auth, TARGETS, TOTAL  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
YEARS = list(range(2016, 2025))
OLD_YEARS = list(range(2016, 2023))
NEW_YEARS = [2023, 2024]

W_OLD = {"w%d" % y: 1 + i for i, y in enumerate(OLD_YEARS)}
S_OLD = {"s%d" % y: 8 + i for i, y in enumerate(OLD_YEARS)}
# לוחות „שכר ממוצע וחציוני”: 2,3 מספר עובדים · 11,12 ממוצע לחודש עבודה · 14,15 חציון
NEW_SAL = {"w2023": 2, "w2024": 3, "s2023": 11, "s2024": 12, "m2023": 14, "m2024": 15}
BANDS = {"b%d" % i: 5 + 2 * i for i in range(1, 8)}          # 2024
BANDS23 = {"b%d" % i: 4 + 2 * i for i in range(1, 8)}        # 2023

# נספח -> (לוח יישובים, לוח מועצות) לכל מהדורה
NEW_T = {"א": (2, 3), "ג": (34, 35), "ו": (82, 83), "ד": (50, 51), "ז": (98, 99), "ח": (114, 115)}
OLD_T = {"א": (3, 6), "ג": (77, 80), "ו": (146, 149), "ד": (100, 103), "ז": (169, 172), "ח": (192, 195)}
DIST_T = {"emp": (43, 45), "self": (91, 93), "all": (11, 13)}

# לוחות „מחוז ונפה” — המקום היחיד שבו יש שורה ארצית אמיתית בשתי המהדורות.
# שורת „סה\"כ” בלוחות היישוב של 2016–2022 היא „סה\"כ יישובים מעל 2,000 תושבים”
# ולא ארצית, ושרשור שלה לשורה הארצית של 2023–2024 היה מייצר קפיצה מדומה.
# מבנה העמודות שונה: תווית כפולה (מחוז + נפה), ולכן המגדר בעמודה 2 והנתונים מוסטים.
NAT_ROW = 'סה"כ- נפה ומחוז'
NAT_OLD_T = {"א": 8, "ג": 82, "ו": 151, "ד": 105, "ז": 174, "ח": 197}
NAT_NEW_T = {"א": 4, "ג": 36, "ו": 84, "ד": 52, "ז": 100, "ח": 116}
NAT_W_OLD = {"w%d" % y: 2 + i for i, y in enumerate(OLD_YEARS)}
NAT_S_OLD = {"s%d" % y: 9 + i for i, y in enumerate(OLD_YEARS)}
NAT_NEW = {"w2023": 3, "w2024": 4, "s2023": 12, "s2024": 13, "m2023": 15, "m2024": 16}

# „label” הוא שם האוכלוסייה; „count” הוא אותה אוכלוסייה כשסופרים אותה.
# „כלל העובדים” אינו נסבל אחרי מספר („91,234 כלל העובדים”) ואינו מקבל ה״א
# הידיעה („מספר הכלל העובדים”) — ולכן לספירה נדרשת צורה נפרדת.
POPULATIONS = [
    {"id": "emp",  "label": "שכירים",       "count": "שכירים", "appendix": "ג׳", "parts": ["ד", "ח"],
     "def": "כל מי שהייתה לו הכנסה מעבודה שכירה, נספרת רק ההכנסה מעבודה שכירה"},
    {"id": "self", "label": "עצמאים",       "count": "עצמאים", "appendix": "ו׳", "parts": ["ז", "ח"],
     "def": "כל מי שהייתה לו הכנסה מעבודה עצמאית, נספרת רק ההכנסה מעבודה עצמאית"},
    {"id": "all",  "label": "כלל העובדים",  "count": "עובדים", "appendix": "א׳", "parts": ["ד", "ז", "ח"],
     "def": "כל מי שהייתה לו הכנסה מעבודה — שכירה, עצמאית או שתיהן"},
]
POP_APPENDIX = {"emp": "ג", "self": "ו", "all": "א"}


def die(msg):
    sys.exit("build_btl.py נכשל: " + msg)


def load():
    new = {ap: {"loc": read(lt, "2023–2024", "loc", NEW_SAL),
                "rc": read(rt, "2023–2024", "rc", NEW_SAL)}
           for ap, (lt, rt) in NEW_T.items()}
    old = {ap: {"loc": read(lt, "2016–2022", "loc", {**W_OLD, **S_OLD}, skip=4, gendered=False),
                "rc": read(rt, "2016–2022", "rc", {**W_OLD, **S_OLD}, skip=4, gendered=False)}
           for ap, (lt, rt) in OLD_T.items()}
    dist = {}
    for pop, (lt, rt) in DIST_T.items():
        dist[pop] = {"loc": (read(lt, "2023–2024", "loc", BANDS),
                             read(lt, "2023–2024", "loc", BANDS23)),
                     "rc": (read(rt, "2023–2024", "rc", BANDS),
                            read(rt, "2023–2024", "rc", BANDS23))}
    return new, old, dist


def headcount(new, old, geo, key, appendix, year):
    """מספר עובדים בנספח בודד, בשנה נתונה. None אם אין נתון."""
    if year in NEW_YEARS:
        row = new[appendix][geo].get(key)
        return row[TOTAL]["w%d" % year] if row and TOTAL in row else None
    row = old[appendix][geo].get(key)
    return row["w%d" % year] if row else None


def salary(new, old, geo, key, appendix, year):
    if year in NEW_YEARS:
        row = new[appendix][geo].get(key)
        return row[TOTAL]["s%d" % year] if row and TOTAL in row else None
    row = old[appendix][geo].get(key)
    return row["s%d" % year] if row else None


def build():
    new, old, dist = load()
    authorities, n_loc, n_rc = [], 0, 0

    for t in TARGETS:
        name, geo = t["official"], geo_of_auth(t["official"])
        # מפתח נפרד לכל נספח ומהדורה — התוויות זהות, אבל אין להניח זאת
        keys_new = {ap: find(name, new[ap][geo]) for ap in NEW_T}
        keys_old = {ap: find(name, old[ap][geo]) for ap in OLD_T}
        if not keys_new.get("ד"):
            authorities.append({"name": name, "rc": geo == "rc", "missing": True})
            continue
        n_rc += geo == "rc"
        n_loc += geo == "loc"

        rec = {"name": name, "rc": geo == "rc", "missing": False,
               "mix": {}, "n": {}, "trend": {}, "median": {}, "dist": {}}

        # --- תמהיל התעסוקה: ד׳ / ז׳ / ח׳ זרים זה לזה, וסכומם הוא „כלל העובדים”
        for year in YEARS:
            keys = keys_new if year in NEW_YEARS else keys_old
            parts = {ap: headcount(new, old, geo, keys[ap], ap, year) for ap in ("ד", "ז", "ח")}
            if any(v is None for v in parts.values()):
                continue
            rec["mix"][str(year)] = {"emp": parts["ד"], "self": parts["ז"], "both": parts["ח"]}
            # בדיקת השלמות מול העמודה שפורסמה — פרט ל-2019 בלוח 3, הידועה כשגויה
            published = headcount(new, old, geo, keys["א"], "א", year)
            derived = sum(parts.values())
            if published is not None and abs(published - derived) > 2 and not (geo == "loc" and year == 2019):
                die("החלוקה א׳=ד׳+ז׳+ח׳ אינה מתלכדת ב%s לשנת %d (פורסם %d, נגזר %d)"
                    % (name, year, published, derived))

        # --- מספרי עובדים ומגמת שכר לכל אוכלוסייה
        for pop in POPULATIONS:
            pid, ap = pop["id"], POP_APPENDIX[pop["id"]]
            rec["n"][pid] = [sum(rec["mix"][str(y)][k] for k in
                                 (("emp", "both") if pid == "emp" else
                                  ("self", "both") if pid == "self" else ("emp", "self", "both")))
                             if str(y) in rec["mix"] else None for y in YEARS]
            rec["trend"][pid] = [salary(new, old, geo,
                                        (keys_new if y in NEW_YEARS else keys_old)[ap], ap, y)
                                 for y in YEARS]
            row = new[ap][geo].get(keys_new[ap])
            rec["median"][pid] = {str(y): (row[TOTAL]["m%d" % y] if row else None) for y in NEW_YEARS}

            # --- התפלגות
            d24, d23 = dist[pid][geo]
            k = find(name, d24)
            rec["dist"][pid] = {}
            for year, table, cols in ((2024, d24, BANDS), (2023, d23, BANDS23)):
                kk = find(name, table)
                if not kk or TOTAL not in table[kk]:
                    rec["dist"][pid][str(year)] = None
                    continue
                vals = [table[kk][TOTAL]["b%d" % i] for i in range(1, 8)]
                if any(v is None for v in vals):
                    rec["dist"][pid][str(year)] = None
                    continue
                if abs(sum(vals) - 100) > 0.35:
                    die("רצועות ההתפלגות ב%s (%s, %d) סוכמות ל-%.1f%%" % (name, pid, year, sum(vals)))
                rec["dist"][pid][str(year)] = [round(v, 1) for v in vals]
        authorities.append(rec)

    if n_loc < 13:
        die("נמצאו %d יישובים בלבד (מצופה 13)" % n_loc)
    if n_rc < 4:
        die("נמצאו %d מועצות אזוריות בלבד (מצופה 4)" % n_rc)

    # ------------------------------------------------ ארצי (מלוחות המחוז)
    nat_old = {ap: read(t, "2016–2022", "district", {**NAT_W_OLD, **NAT_S_OLD},
                        skip=4, gendered=False)[NAT_ROW]
               for ap, t in NAT_OLD_T.items()}
    nat_new = {ap: read(t, "2023–2024", "district", NAT_NEW,
                        gendered=True, gender_col=2)[NAT_ROW][TOTAL]
               for ap, t in NAT_NEW_T.items()}

    def nat(ap, prefix, year):
        return (nat_new if year in NEW_YEARS else nat_old)[ap]["%s%d" % (prefix, year)]

    national = {"mix": {}, "n": {}, "trend": {}, "median": {}, "dist": {}}
    for year in YEARS:
        parts = {ap: nat(ap, "w", year) for ap in ("ד", "ז", "ח")}
        if any(v is None for v in parts.values()):
            continue
        national["mix"][str(year)] = {"emp": parts["ד"], "self": parts["ז"], "both": parts["ח"]}
        published = nat("א", "w", year)
        if published is not None and abs(published - sum(parts.values())) > 2:
            die("החלוקה הארצית אינה מתלכדת ב-%d (פורסם %d, נגזר %d)"
                % (year, published, sum(parts.values())))
    for pop in POPULATIONS:
        pid, ap = pop["id"], POP_APPENDIX[pop["id"]]
        national["n"][pid] = [nat(ap, "w", y) for y in YEARS]
        national["trend"][pid] = [nat(ap, "s", y) for y in YEARS]
        national["median"][pid] = {str(y): nat_new[ap]["m%d" % y] for y in NEW_YEARS}
        d24, d23 = dist[pid]["loc"]
        national["dist"][pid] = {
            "2024": [round(d24[TOTAL][TOTAL]["b%d" % i], 1) for i in range(1, 8)],
            "2023": [round(d23[TOTAL][TOTAL]["b%d" % i], 1) for i in range(1, 8)]}

    # ------------------------------------------------ אשכול — בסיס רשויות קבוע
    present = [a for a in authorities if not a["missing"]]
    base = [a for a in present if all(a["mix"].get(str(y)) for y in YEARS)]
    if not base:
        die("אין אף רשות עם סדרה מלאה — לא ניתן לחשב אשכול על בסיס קבוע")
    cluster = {"base": [a["name"] for a in base], "excluded": [
        {"name": a["name"], "why": "אין נתון בכל השנים" if not a["missing"] else "מתחת לסף 2,000 תושבים"}
        for a in authorities if a not in base],
        "mix": {}, "n": {}, "trend": {}, "dist": {}, "median": {}}
    for year in YEARS:
        agg = {"emp": 0, "self": 0, "both": 0}
        for a in base:
            for k in agg:
                agg[k] += a["mix"][str(year)][k]
        cluster["mix"][str(year)] = agg
    for pop in POPULATIONS:
        pid = pop["id"]
        cluster["n"][pid] = [sum(cluster["mix"][str(y)][k] for k in
                                 (("emp", "both") if pid == "emp" else
                                  ("self", "both") if pid == "self" else ("emp", "self", "both")))
                             for y in YEARS]
        series = []
        for i, y in enumerate(YEARS):
            num = den = 0.0
            for a in base:
                v, w = a["trend"][pid][i], a["n"][pid][i]
                if v and w:
                    num += v * w
                    den += w
            series.append(round(num / den) if den else None)   # שקלול לפי מספר אנשים
        cluster["trend"][pid] = series
        # התפלגות: ממוצע משוקלל של האחוזים לפי מספר אנשים
        cluster["dist"][pid] = {}
        for year in NEW_YEARS:
            i = YEARS.index(year)
            acc, den = [0.0] * 7, 0.0
            for a in base:
                b, w = a["dist"][pid].get(str(year)), a["n"][pid][i]
                if b and w:
                    den += w
                    for j in range(7):
                        acc[j] += b[j] * w
            cluster["dist"][pid][str(year)] = [round(x / den, 1) for x in acc] if den else None

    out = {
        "meta": {
            "source": "המוסד לביטוח לאומי",
            "years": YEARS, "distYears": NEW_YEARS,
            "tables": {"תמהיל התעסוקה": "50/51 · 98/99 · 114/115 (2023–2024) · 100/103 · 169/172 · 192/195 (2016–2022)",
                       "התפלגות השכר": "43/45 · 91/93 · 11/13 (2023–2024)",
                       "מגמת השכר": "34/35 · 82/83 · 2/3 (2023–2024) · 77/80 · 146/149 · 3/6 (2016–2022)"},
            "measure": "שכר ממוצע לחודש עבודה",
            "note": ("נתוני חלק זה הם של המוסד לביטוח לאומי, ואינם ניתנים להשוואה ישירה "
                     "לערכי הלמ\"ס שבחלק א׳ — רמת השכר נבדלת ב-8.7%–27.2% באותה אוכלוסייה."),
        },
        "populations": POPULATIONS,
        "authorities": authorities,
        "national": national,
        "cluster": cluster,
    }
    path = os.path.join(HERE, "btl.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print("נכתב %s (%s bytes)" % (path, format(os.path.getsize(path), ",")))
    print("  רשויות: %d יישובים + %d מועצות · חסרות: %s"
          % (n_loc, n_rc, [a["name"] for a in authorities if a["missing"]]))
    print("  בסיס האשכול: %d רשויות · לא נכללו: %s"
          % (len(base), [e["name"] for e in cluster["excluded"]]))
    print("  שיעור עצמאים באשכול 2024: %.1f%%  ארצי: %.1f%%"
          % (100 * (cluster["mix"]["2024"]["self"] + cluster["mix"]["2024"]["both"])
             / sum(cluster["mix"]["2024"].values()),
             100 * (national["mix"]["2024"]["self"] + national["mix"]["2024"]["both"])
             / sum(national["mix"]["2024"].values())))


if __name__ == "__main__":
    build()
