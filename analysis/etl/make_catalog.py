# -*- coding: utf-8 -*-
"""Catalogue every table in relevant_tables.rar: family, geography, population,
income concept, years, metrics, and whether it survived extraction."""
import os, re, zipfile
import pandas as pd
from build_master import population, concept, geo_level

D = '/d/relevant_tables'
M = pd.read_pickle('/d/work/master.pkl')


def family(stem):
    for pat, fam in [
        (r'^שכר ממוצע וחציוני',      'שכר ממוצע וחציוני'),
        (r'^שכר ממוצע לחודש בשנה',   'שכר ממוצע לחודש בשנה'),
        (r'^שכר ממוצע לחודש עבודה',  'שכר ממוצע לחודש עבודה'),
        (r'^משך העבודה',             'משך העבודה'),
        (r'^קבוצת ההכנסה',           'קבוצת ההכנסה'),
        (r'^אחוז',                   'אחוז עד שכר מינימום'),
        (r'^סוג המבוטחים',           'סוג המבוטחים'),
    ]:
        if re.match(pat, stem):
            return fam
    return 'אחר'


# enumerate from the archive listing, not the disk: eight tables have filenames
# too long for the filesystem and never unpacked, but are still real tables.
ARCHIVE = [l.rstrip('\n') for l in open('/d/work/archive_list.txt', encoding='utf-8')]
rows = []
for f in sorted(ARCHIVE):
    stem = f[:-5]
    p = os.path.join(D, f)
    try:
        ok = zipfile.ZipFile(p).testzip() is None
    except Exception:
        ok = False
    on_disk = os.path.exists(p)
    sub = M[M.src == stem]
    rows.append(dict(
        קובץ=stem,
        משפחה=family(stem),
        רמה_גאוגרפית=geo_level(stem),
        אוכלוסייה=population(stem),
        מושג_הכנסה=concept(stem),
        פילוח_מגדר='כן' if ('מין' in stem or 'מגדר' in stem) else 'לא',
        שנים=','.join(str(int(y)) for y in sorted(sub.year.unique())) if len(sub) else '',
        מדדים=','.join(sorted(sub.mkey.unique())) if len(sub) else '',
        שורות=len(sub),
        ישויות=sub.entity.nunique() if len(sub) else 0,
        נחלץ_בהצלחה='כן' if (on_disk and ok) else 'לא',
        סיבת_כשל=('' if (on_disk and ok) else
                  ('שם קובץ ארוך מדי' if not on_disk else 'דחיסה לא נתמכת/פגום')),
        מקור_בפועל=('xlsx' if len(sub) and not sub.backfilled.all()
                    else ('unified_all.csv' if len(sub) else 'חסר')),
    ))
cat = pd.DataFrame(rows)
cat.to_csv('/d/work/out/btl-table-catalog.csv', index=False, encoding='utf-8-sig')
print('tables in archive:', len(cat))
print(cat.groupby(['משפחה', 'רמה_גאוגרפית']).size().unstack(fill_value=0).to_string())
print('\nמקור בפועל:', cat.מקור_בפועל.value_counts().to_dict())
print('לא נחלצו בהצלחה:', (cat.נחלץ_בהצלחה == 'לא').sum(), cat.סיבת_כשל.value_counts().to_dict())
print('\nטבלאות שאבדו לגמרי:')
for s in cat[cat.מקור_בפועל == 'חסר'].קובץ:
    print('  -', s[:100])
