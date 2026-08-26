# -*- coding: utf-8 -*-
"""
בונה את קובץ הנתונים של הדשבורד מתוך קובצי המקור.

קלט   : "עיבוד לפי ענף ורשות בני דורמבט.xlsx"  (למ"ס, עיבוד מרכז הידע)
        "dicAnaf4SfarotMaster 2.xlsx"          (מילון ענפי כלכלה, למ"ס)
פלט   : dashboard/data.json  +  הזרקה ל-index.html / artifact.html דרך build.py

הרצה  : python3 dashboard/build_data.py
"""
import json, os, sys
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DATA = os.path.join(ROOT, "עיבוד לפי ענף ורשות בני דורמבט.xlsx")
SRC_DIC  = os.path.join(ROOT, "dicAnaf4SfarotMaster 2.xlsx")

# --- שמות תצוגה קצרים לקבוצות הענפים (54 קודים דו-ספרתיים ב-51 קבוצות) -------
# נגזרו ממילון ענפי הכלכלה של הלמ"ס; קוצרו כדי שייקראו היטב על גבי גרף.
ANAF_LABELS = {
    "1":              "גידולים צמחיים",
    "2+3+4":          "בעלי חיים, דיג וייעור",
    "5+6+7+8":        "כרייה וחציבה",
    "10":             "ייצור מוצרי מזון",
    "11+12":          "ייצור משקאות וטבק",
    "13+14+15":       "טקסטיל, הלבשה ועור",
    "16+17+18":       "עץ, נייר ודפוס",
    "19+20":          "נפט מזוקק וכימיקלים",
    "21":             "ייצור תרופות",
    "22":             "גומי ופלסטיק",
    "23+24+25":       "מינרלים אל-מתכתיים ומתכת",
    "26":             "מחשבים, אלקטרוניקה ואופטיקה",
    "27+28":          "ציוד חשמלי ומכונות",
    "29+30":          "כלי רכב וכלי תחבורה",
    "31+32+33+34":    "רהיטים, יהלומים וייצור אחר",
    "35+36+37+38+39": "חשמל, מים וטיפול בפסולת",
    "41":             "בניית מבנים ובניינים",
    "42":             "עבודות הנדסה אזרחית",
    "43":             "עבודות בנייה מיוחדות",
    "45":             "מסחר ותיקון כלי רכב",
    "46":             "מסחר סיטוני",
    "47":             "מסחר קמעוני",
    "49":             "הובלה יבשתית",
    "50+51+52+53":    "הובלה ימית ואווירית, אחסנה ודואר",
    "55":             "שירותי אירוח",
    "56":             "מסעדות ושירותי מזון",
    "58+59+60":       "הוצאה לאור, קולנוע ושידור",
    "61":             "שירותי תקשורת",
    "62+63":          "תכנות, ייעוץ ושירותי מידע",
    "64+65+66":       "שירותים פיננסיים וביטוח",
    "68":             "פעילויות בנדל\"ן",
    "69":             "שירותים משפטיים וחשבונאות",
    "70":             "ייעוץ ניהולי ומשרדים ראשיים",
    "71":             "אדריכלות, הנדסה ובדיקות טכניות",
    "72":             "מחקר מדעי ופיתוח",
    "73+74+75":       "פרסום ושירותים מקצועיים אחרים",
    "77+79":          "השכרה וסוכנויות נסיעות",
    "78":             "שירותי תעסוקה",
    "80":             "שמירה ואבטחה",
    "81":             "תחזוקת בניינים וגינון",
    "82":             "ניהול ותמיכה למשרדים ולעסקים",
    "83":             "מינהל מקומי",
    "84":             "מינהל ציבורי, ביטחון וביטוח לאומי",
    "85":             "חינוך",
    "86":             "שירותי בריאות",
    "87+88":          "רווחה, סעד ומגורים טיפוליים",
    "90+91+92":       "אמנות, תרבות ובידור",
    "93":             "ספורט, בילוי ופנאי",
    "94":             "ארגוני חברים",
    "95+96":          "תיקון ושירותים אישיים",
    "97+98+99":       "משקי בית כמעסיקים וארגונים חוץ-מדינתיים",
}

# --- קיבוצים (clusters) ------------------------------------------------------
# ברירת המחדל: סדרי הענפים של הלמ"ס (אותיות A–U), מאוחדים לקיבוצים קריאים.
# "היי-טק" הוא קיבוץ חוצה-סדרים לפי הגדרת הלמ"ס, ולכן חופף לקיבוצים אחרים.
CLUSTERS = [
    ("agri",    "חקלאות, ייעור ודיג",        ["1", "2+3+4"]),
    ("infra",   "אנרגיה, מים, פסולת וכרייה",  ["5+6+7+8", "35+36+37+38+39"]),
    ("manuf",   "תעשייה וייצור",              ["10", "11+12", "13+14+15", "16+17+18", "19+20", "21", "22",
                                               "23+24+25", "26", "27+28", "29+30", "31+32+33+34"]),
    ("constr",  "בינוי",                      ["41", "42", "43"]),
    ("trade",   "מסחר",                       ["45", "46", "47"]),
    ("transp",  "תחבורה, אחסנה ודואר",         ["49", "50+51+52+53"]),
    ("hosp",    "אירוח ומזון",                ["55", "56"]),
    ("ict",     "מידע ותקשורת",               ["58+59+60", "61", "62+63"]),
    ("fin",     "פיננסים, ביטוח ונדל\"ן",      ["64+65+66", "68"]),
    ("prof",    "שירותים מקצועיים ומדעיים",    ["69", "70", "71", "72", "73+74+75"]),
    ("admin",   "שירותי ניהול ותמיכה",         ["77+79", "78", "80", "81", "82"]),
    ("public",  "מינהל מקומי וציבורי",         ["83", "84"]),
    ("edu",     "חינוך",                      ["85"]),
    ("health",  "בריאות, רווחה וסעד",          ["86", "87+88"]),
    ("other",   "אמנות, פנאי ושירותים אחרים",  ["90+91+92", "93", "94", "95+96", "97+98+99"]),
    ("hitech",  "היי-טק (תעשייה ושירותים)",    ["21", "26", "61", "62+63", "72"]),
]

NAFOT = {  # שיוך רשות לנפה — נגזר מסדר הגיליון ומאומת מול סכומי הנפות
    "נפת צפת": ["ראש פינה", "יסוד המעלה", "מטולה", "ג'ש (גוש חלב)", "טובא-זנגרייה",
                "חצור הגלילית", "קריית שמונה", "הגליל העליון", "מרום הגליל",
                "מבואות החרמון", "צפת"],
    "נפת גולן": ["בוקעאתא", "קצרין", "מג'דל שמס", "מסעדה", "ע'ג'ר", "עין קנייא", "גולן"],
}


def num(v):
    return round(v, 4) if isinstance(v, (int, float)) else None


def read_dictionary():
    """מחזיר מיפוי קוד דו-ספרתי → {שם, סדר ענפים}."""
    wb = openpyxl.load_workbook(SRC_DIC, data_only=True)
    ws = wb["רשימת הערכים במילון ענפי כלכלה"]
    rows = list(ws.iter_rows(values_only=True))
    ix = {str(h).strip(): i for i, h in enumerate(rows[0]) if h}
    out = {}
    for r in rows[1:]:
        code = r[ix["SemelAnaf2Sfarot"]]
        if code is None:
            continue
        code = str(code).strip()
        if code in out:
            continue
        out[code] = {
            "name": (r[ix["ShemAnaf2Sfarot"]] or "").strip(),
            "seder": (r[ix["ShemSederAnafOt"]] or "").strip(),
            "letter": (r[ix["SemelSederAnafOt"]] or "").strip(),
        }
    wb.close()
    return out


def read_authorities(wb):
    ws = wb["לפי רשויות בנפת צפת וגולן"]
    rows = list(ws.iter_rows(values_only=True))
    of_nafa = {name: nafa for nafa, names in NAFOT.items() for name in names}

    national = rows[2]           # סך כללי (באלפים)
    nafot = []
    for r in rows[3:5]:
        nafot.append({"name": r[1].strip(), "workers": num(r[3]),
                      "months": num(r[4]), "salary": num(r[5])})

    items = []
    for r in rows[5:23]:
        name = (r[2] or "").strip()
        if not name:
            continue
        if name not in of_nafa:
            sys.exit(f"רשות לא מוכרת בשיוך לנפה: {name}")
        items.append({"name": name, "nafa": of_nafa[name], "workers": num(r[3]),
                      "months": num(r[4]), "salary": num(r[5])})

    # אימות: סכום השכירים ברשויות חייב להתאים לסכום הנפות
    for nf in nafot:
        s = sum(i["workers"] for i in items if i["nafa"] == nf["name"])
        assert abs(s - nf["workers"]) < 1, f"{nf['name']}: {s} != {nf['workers']}"

    total_w = sum(i["workers"] for i in items)
    region = {
        "name": "נפות צפת וגולן",
        "workers": total_w,
        "salary": round(sum(i["workers"] * i["salary"] for i in items) / total_w, 2),
        "months": round(sum(i["workers"] * i["months"] for i in items) / total_w, 3),
    }
    return {
        "items": items,
        "nafot": nafot,
        "region": region,
        "national": {"name": "ממוצע ארצי", "workers": round(national[3] * 1000),
                     "months": num(national[4]), "salary": num(national[5])},
    }


def read_anafim(wb, dic):
    ws = wb["לפי ענף כלכלי"]
    rows = list(ws.iter_rows(values_only=True))
    items = []
    for r in rows[3:54]:
        code = str(r[1]).strip()
        if not code or code == "None":
            continue
        codes = [c.strip().zfill(2) for c in code.split("+")]
        seders, parts = [], []
        for c in codes:
            d = dic.get(c)
            if not d:
                sys.exit(f"קוד ענף חסר במילון: {c}")
            if d["seder"] and d["seder"] not in seders:
                seders.append(d["seder"])
            parts.append(d["name"])
        if code not in ANAF_LABELS:
            sys.exit(f"חסר שם תצוגה לקבוצת הענפים: {code}")
        items.append({
            "code": code,
            "label": ANAF_LABELS[code],
            "seder": " · ".join(seders),
            "parts": parts,
            "nat": {"workers": num(r[2]), "months": num(r[3]), "salary": num(r[4])},
            "reg": {"workers": num(r[5]), "months": num(r[6]), "salary": num(r[7])},
        })

    known = {i["code"] for i in items}
    for cid, cname, codes in CLUSTERS:
        missing = [c for c in codes if c not in known]
        if missing:
            sys.exit(f"קיבוץ {cid}: קודים שאינם בנתונים {missing}")
    return items


def main():
    dic = read_dictionary()
    wb = openpyxl.load_workbook(SRC_DATA, data_only=True)
    authorities = read_authorities(wb)
    anafim = read_anafim(wb, dic)
    wb.close()

    data = {
        "meta": {
            "year": "2024",
            "source": 'הלשכה המרכזית לסטטיסטיקה — עיבוד מיוחד מתוך קובצי הכנסה מנהליים',
            "processing": "עיבוד: מרכז הידע האזורי גליל מזרחי | מערבי",
        },
        "metrics": [
            {"id": "salary",  "label": "שכר חודשי ממוצע",   "short": "שכר",         "unit": "₪",     "dec": 0},
            {"id": "workers", "label": "מספר שכירים",        "short": "שכירים",      "unit": "",      "dec": 0},
            {"id": "months",  "label": "ממוצע חודשי עבודה",  "short": "חודשי עבודה", "unit": "חודשים", "dec": 2},
        ],
        "authorities": authorities,
        "anafim": anafim,
        "clusters": [{"id": c, "label": l, "codes": codes} for c, l, codes in CLUSTERS],
    }

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    reg_sum = sum(i["reg"]["workers"] for i in anafim if isinstance(i["reg"]["workers"], (int, float)))
    nat_sum = sum(i["nat"]["workers"] for i in anafim if isinstance(i["nat"]["workers"], (int, float)))
    print(f"נכתב {out}")
    print(f"  רשויות: {len(authorities['items'])} · ענפים: {len(anafim)} · קיבוצים: {len(CLUSTERS)}")
    print(f"  כיסוי שכירים לפי ענף — אזור {reg_sum:,} מתוך {authorities['region']['workers']:,}"
          f" · ארצי {nat_sum:,} מתוך {authorities['national']['workers']:,}")


if __name__ == "__main__":
    main()
