# -*- coding: utf-8 -*-
"""בדיקות שלמות על לוחות הביטוח הלאומי — משחזר את הטענות שב-docs/dashboard-architecture.md.

    export BTL_DIR=/path/to/relevant_tables
    python3 scripts/btl_verify.py

יוצא בקוד 1 אם בדיקה נכשלה שלא כצפוי. שגיאת 2019 הידועה בלוח 3 מדווחת כ„צפוי”.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from btl_read import read, find, geo_of_auth, TARGETS, TOTAL, PARTS  # noqa: E402

YEARS_OLD = list(range(2016, 2023))
W_OLD = {"w%d" % y: 1 + i for i, y in enumerate(YEARS_OLD)}
W_NEW = {"w2023": 2, "w2024": 3}

# (מספר לוח ליישובים, מספר לוח למועצות) לכל נספח
NEW_TABLES = {"א": (2, 3), "ד": (50, 51), "ז": (98, 99), "ח": (114, 115),
              "ג": (34, 35), "ו": (82, 83)}
OLD_TABLES = {"א": (3, 6), "ד": (100, 103), "ז": (169, 172), "ח": (192, 195),
              "ג": (77, 80), "ו": (146, 149)}

failures = []


def check(name, ok, detail=""):
    print(("  ✅ " if ok else "  ❌ ") + name + (("  — " + detail) if detail else ""))
    if not ok:
        failures.append(name)


def head(t):
    print("\n" + t + "\n" + "-" * len(t))


# ---------------------------------------------------------------- 1
head("1 · החלוקה א׳ = ד׳ + ז׳ + ח׳ (מהדורת 2023–2024)")
new = {ap: {"loc": read(lt, "2023–2024", "loc", W_NEW),
            "rc": read(rt, "2023–2024", "rc", W_NEW)}
       for ap, (lt, rt) in NEW_TABLES.items()}

for year in ("w2023", "w2024"):
    total = new["א"]["loc"][TOTAL][TOTAL][year]
    parts = sum(new[ap]["loc"][TOTAL][TOTAL][year] for ap in PARTS)
    check("ארצי %s" % year[1:], abs(total - parts) <= 1,
          "א׳=%s  ד+ז+ח=%s" % (format(total, ",.0f"), format(parts, ",.0f")))

bad, seen, missing = [], 0, []
for t in TARGETS:
    nm, geo = t["official"], geo_of_auth(t["official"])
    keys = {ap: find(nm, new[ap][geo]) for ap in ("א",) + PARTS}
    if not all(keys.values()):
        missing.append(nm)
        continue
    seen += 1
    vals = {ap: new[ap][geo][keys[ap]][TOTAL]["w2024"] or 0 for ap in keys}
    if abs(vals["א"] - sum(vals[ap] for ap in PARTS)) > 1:
        bad.append(nm)
check("כל רשויות האשכול 2024", not bad, "%d/%d נבדקו · חסרות: %s" % (seen, len(TARGETS), missing))

# ---------------------------------------------------------------- 2
head("2 · האיחודים: ג׳ = ד׳+ח׳ · ו׳ = ז׳+ח׳")
for ap, comp in (("ג", ("ד", "ח")), ("ו", ("ז", "ח"))):
    v = new[ap]["loc"][TOTAL][TOTAL]["w2024"]
    s = sum(new[c]["loc"][TOTAL][TOTAL]["w2024"] for c in comp)
    check("%s׳ = %s" % (ap, "+".join(c + "׳" for c in comp)), abs(v - s) <= 1,
          "%s מול %s" % (format(v, ",.0f"), format(s, ",.0f")))

# ---------------------------------------------------------------- 3
head("3 · שחזור „סוג המבוטחים” מול הלוח שפורסם (2022)")
old = {ap: {"loc": read(lt, "2016–2022", "loc", W_OLD, skip=4, gendered=False),
            "rc": read(rt, "2016–2022", "rc", W_OLD, skip=4, gendered=False)}
       for ap, (lt, rt) in OLD_TABLES.items()}
pub = read(234, "?", "rc", {"all": 1, "emp": 2, "self": 3, "both": 4},
           skip=4, gendered=False)
for t in TARGETS:
    if t["form"] != "מועצה אזורית":
        continue
    nm = t["official"]
    kp = find(nm, pub)
    ko = {ap: find(nm, old[ap]["rc"]) for ap in ("א",) + PARTS}
    if not kp or not all(ko.values()):
        check(nm, False, "לא נמצא")
        continue
    p, r = pub[kp], {ap: old[ap]["rc"][ko[ap]]["w2022"] for ap in ko}
    same = all(abs(a - b) <= 1 for a, b in
               ((r["א"], p["all"]), (r["ד"], p["emp"]),
                (r["ז"], p["self"]), (r["ח"], p["both"])))
    check(nm, same, "כלל %s · שכירים %s · עצמאים %s · משולב %s"
          % tuple(format(r[ap], ",.0f") for ap in ("א",) + PARTS))

# ---------------------------------------------------------------- 4
head("4 · שגיאת 2019 בלוח 3 — היקף ידוע וצפוי")
for geo, label in (("loc", "יישובים"), ("rc", "מועצות אזוריות")):
    for year in YEARS_OLD:
        col = "w%d" % year
        off = 0
        for lab in old["א"][geo]:
            if any(lab not in old[ap][geo] for ap in PARTS):
                continue
            a = old["א"][geo][lab][col]
            parts = [old[ap][geo][lab][col] for ap in PARTS]
            if a is None or any(p is None for p in parts):
                continue
            if abs(a - sum(parts)) > 2:
                off += 1
        expected = 49 if (geo == "loc" and year == 2019) else 0
        check("%s %d — %d שורות חורגות" % (label, year, off), off == expected,
              "צפוי %d" % expected)

# ---------------------------------------------------------------- 5
head("5 · רצועות ההתפלגות סוכמות ל-100%")
bands = {"b%d" % i: 5 + 2 * i for i in range(1, 8)}
for num, geo, who in ((43, "loc", "שכירים · יישובים"), (45, "rc", "שכירים · מ.א."),
                      (91, "loc", "עצמאים · יישובים"), (93, "rc", "עצמאים · מ.א.")):
    dist = read(num, "2023–2024", geo, bands)
    worst, worst_lab = 0.0, ""
    for t in TARGETS:
        if geo_of_auth(t["official"]) != geo:
            continue
        k = find(t["official"], dist)
        if not k:
            continue
        vals = [dist[k][TOTAL]["b%d" % i] for i in range(1, 8)]
        if any(v is None for v in vals):
            worst, worst_lab = 99, t["official"] + " (השמטה)"
            break
        d = abs(sum(vals) - 100)
        if d > worst:
            worst, worst_lab = d, t["official"]
    check("לוח %d · %s" % (num, who), worst <= 0.2,
          "סטייה מרבית %.1f נק׳ (%s)" % (worst, worst_lab))

print("\n" + ("כל הבדיקות עברו." if not failures
             else "נכשלו %d בדיקות: %s" % (len(failures), failures)))
sys.exit(1 if failures else 0)
