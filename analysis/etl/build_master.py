# -*- coding: utf-8 -*-
"""Assemble the analysis master from the re-parsed BTL tables.

  1. normalise metric names to canonical keys
  2. lift the gender-in-column-header family into the gender dimension
  3. derive the population / income-concept dimensions from the table name
  4. back-fill the 15 archive-corrupt tables from unified_all.csv (with its
     district/sub-district columns put back where they belong)
  5. tag every row with its geography level and Eastern-Galilee cluster membership
"""
import re, sys
import numpy as np
import pandas as pd

sys.path.insert(0, '/home/user/CBSaleryEastGallile/eshkol-matching')
from eshkol_matcher import sanitize

MAP = '/home/user/CBSaleryEastGallile/eshkol-matching/eshkol_mapping.xlsx'

# ---------------------------------------------------------------- metric keys
METRIC_RULES = [
    (r'חודש בשנה \| ממוצע$|^השכר הממוצע \(₪\) לחודש בשנה$|ממוצע לחודש בשנה \| ממוצע$', 'wage_year_mean'),
    (r'חודש בשנה \| חציון$|ממוצע לחודש בשנה \| חציון$',                                  'wage_year_med'),
    (r'חודש עבודה \| ממוצע$|^השכר הממוצע \(₪\) לחודש עבודה$|ממוצע לחודש עבודה \| ממוצע$', 'wage_work_mean'),
    (r'חודש עבודה \| חציון$|ממוצע לחודש עבודה \| חציון$',                                 'wage_work_med'),
    (r'אחוז העובדים המשתכרים עד שכר המינימום \| לפי ממוצע לחודש בשנה',  'pct_minwage_year'),
    (r'אחוז העובדים המשתכרים עד שכר המינימום \| לפי ממוצע לחודש עבודה', 'pct_minwage_work'),
    (r'^אחוז השכירים.*מינימום|^אחוז העצמאים.*מינימום',                  'pct_minwage_sub'),
    # 'סוג המבוטחים' tables: counts and shares of the insured by work status
    (r'^כמות \| כלל העובדים',      'n_workers'),
    (r'^כמות \| שכירים בלבד',      'n_emp_only'),
    (r'^כמות \| עצמאים בלבד',      'n_self_only'),
    (r'^כמות \| שכירים ועצמאים',   'n_both'),
    (r'^אחוזים \| שכירים בלבד',    'pct_emp_only'),
    (r'^אחוזים \| עצמאים בלבד',    'pct_self_only'),
    (r'^אחוזים \| שכירים ועצמאים', 'pct_both'),
    (r'^אחוזים \| כלל העובדים',    'drop'),
    # in the 'קבוצת ההכנסה' tables the wage column carries only the basis as header
    # unified_all.csv appends ' - מספר עובדים' to every column label in these
    # tables, wage columns included, so the suffix is optional here
    (r'^ממוצע לחודש בשנה( - מספר עובדים)?$',  'wage_year_mean'),
    (r'^ממוצע לחודש עבודה( - מספר עובדים)?$', 'wage_work_mean'),
    (r'משך העבודה .* 1-2 חודשים',   'dur_1_2'),
    (r'משך העבודה .* 3-5 חודשים',   'dur_3_5'),
    (r'משך העבודה .* 6-8 חודשים',   'dur_6_8'),
    (r'משך העבודה .* 9-11 חודשים',  'dur_9_11'),
    (r'משך העבודה .* 12 חודשים',    'dur_12'),
    (r'ממוצע חודשי עבודה',          'months_avg'),
    (r'^אחוז המשתכרים עד שכר המינימום', 'inc_minwage'),
    (r'^עד 75% מהשכר הממוצע',        'inc_le75'),
    (r'^עד השכר הממוצע',             'inc_le100'),
    (r'^עד פעמיים השכר הממוצע',      'inc_le2x'),
    (r'^עד 3 פעמים השכר הממוצע',     'inc_le3x'),
    (r'^עד 4 פעמים השכר הממוצע',     'inc_le4x'),
    (r'^יותר מ-4 פעמים השכר הממוצע', 'inc_gt4x'),
    (r'^מספר השכירים שאינם עצמאים$|שכירים שאינם גם עצמאים \| מספר',      'n_emp_only'),
    (r'^מספר העצמאים שאינם שכירים$|עצמאים שאינם גם שכירים \| מספר',      'n_self_only'),
    (r'^מספר השכירים שהינם גם עצמאים$|^שכירים ועצמאים \| מספר',          'n_both'),
    (r'^מספר השכירים$',                                                  'n_emp'),
    (r'^מספר העצמאים$',                                                  'n_self'),
    (r'מספר עובדות$|מספר עובדים$|^מספר העובדים$|^מספר כלל העובדים$',      'n_workers'),
]


def norm_metric(m):
    for pat, key in METRIC_RULES:
        if re.search(pat, m):
            return key
    return None


# ------------------------------------------------------- population / concept
def population(src):
    m = re.search(r'\sשל\s(.+?),\s*(?:לפי|\d{4})', src)
    if m:
        p = m.group(1)
    elif src.startswith('אחוז'):
        p = re.sub(r'^אחוז\s', '', src.split(',')[0])
        p = re.sub(r'\s*ש?שכרם.*$', '', p)
    elif src.startswith('סוג המבוטחים'):
        p = 'כלל העובדים'
    else:
        p = '?'
    return re.sub(r'\s*\(.*?\)\s*', ' ', p).strip()


def concept(src):
    m = re.search(r'\(הכנסה (מעבודה[^,)]*)', src)
    if m:
        return m.group(1).strip()
    return 'כל מקורות ההכנסה'


def geo_level(src):
    if 'לפי מחוז' in src:
        return 'נפה/מחוז'
    if 'מועצה איזורית' in src or 'מועצה אזורית' in src:
        return 'מועצה אזורית'
    return 'יישוב'


def reconcile_counts(df):
    """Drop head-count cells that a table contradicts within its own time series.

    'שכר ממוצע לחודש עבודה ... לפי יישוב, 2022-2016' publishes a corrupt 2019
    worker-count column: 50 of its 271 rows carry a value belonging to a different
    locality (מסעדה reads 12,652 between 1,765 and 1,842; its twin table reads
    1,794).  Rather than patch that one file, flag any count that departs from the
    geometric mean of its own neighbouring years by more than 2x while those
    neighbours agree with each other to within 25% - a workforce does not multiply
    and revert in a single year.  Flagged cells are dropped, so the value survives
    from whichever other table reports the same cell.
    """
    key = ['src', 'level', 'entity', 'population', 'concept', 'gender']
    c = df[(df.mkey == 'n_workers') & df.level.isin(['יישוב', 'מועצה אזורית'])]
    ser = c.groupby(key + ['year'], observed=True).value.median().rename('v').reset_index()
    ser = ser.sort_values(key + ['year'])
    g = ser.groupby(key, observed=True).v
    prev, nxt = g.shift(1), g.shift(-1)
    neigh = np.sqrt(prev * nxt)
    stable = (prev / nxt).between(0.8, 1.25)
    flag = (stable & (neigh > 0) & ((ser.v / neigh > 2) | (ser.v / neigh < 0.5))).fillna(False)
    bad = ser[flag][key + ['year']]
    if bad.empty:
        return df
    # drop only the head-count cell, never the wage columns of the same row-set
    r = df.reset_index()
    idx = r[r.mkey == 'n_workers'].merge(bad, on=key + ['year'])['index']
    rep = df.loc[idx].groupby(['src', 'year']).size().sort_values(ascending=False)
    print('integrity: dropped %d implausible head-count cells' % len(idx))
    for (src, yr), k in rep.items():
        print('   %d cells | %d | %s' % (k, yr, src[:78]))
    return df.drop(index=idx)


def main():
    df = pd.read_pickle('/d/work/btl_reparsed.pkl')

    # gender carried in the column header (the 'לפי מגדר ולפי יישוב' family)
    hdr_sex = df.metric.str.extract(r'מגדר \| (זכר|נקבה)')[0]
    df.loc[hdr_sex.notna(), 'gender'] = hdr_sex[hdr_sex.notna()].map({'זכר': 'גברים', 'נקבה': 'נשים'})
    df['metric'] = df.metric.str.replace(r'^מגדר \| (?:זכר|נקבה) \| ', '', regex=True)

    df['mkey'] = df.metric.map(norm_metric)
    unmapped = df[df.mkey.isna()]
    if len(unmapped):
        print('UNMAPPED metrics:', unmapped.metric.value_counts().to_dict())
    df = df[df.mkey.notna() & (df.mkey != 'drop')].copy()

    # ---- back-fill the archive-corrupt tables from unified_all.csv -------------
    u = pd.read_csv('/d/relevant_tables/unified_all.csv', encoding='utf-8-sig')
    u.columns = ['src', 'year', 'area', 'gender', 'metric', 'value']
    missing = sorted(set(u.src) - set(df.src))
    u = u[u.src.isin(missing)].copy()
    is_dist = u.src.map(lambda s: 'לפי מחוז' in s)
    sexes = {'סה"כ', 'גברים', 'נשים'}
    # in district tables unified_all wrote the sub-district into the gender column
    u['geo1'] = u.area
    u['geo2'] = None
    sub = is_dist & ~u.gender.isin(sexes)
    u.loc[sub, 'geo2'] = u.loc[sub, 'gender']
    u.loc[is_dist & u.gender.isin(sexes), 'geo2'] = 'סה"כ'
    u.loc[is_dist, 'gender'] = 'סה"כ'          # gender split was destroyed upstream
    u['mkey'] = u.metric.str.replace(r'\s+', ' ', regex=True).map(norm_metric)
    u = u[u.mkey.notna() & (u.mkey != 'drop')]
    u['backfilled'] = True
    df['backfilled'] = False
    df = pd.concat([df, u[['geo1', 'geo2', 'gender', 'year', 'metric', 'value',
                           'src', 'mkey', 'backfilled']]], ignore_index=True)
    print('back-filled %d tables / %s rows from unified_all.csv' % (len(missing), format(len(u), ',')))

    # ---- dimensions -------------------------------------------------------------
    # the same sub-district appears with a line break or a spelling variant
    for c in ('geo1', 'geo2'):
        df[c] = (df[c].astype('string').str.replace(r'\s+', ' ', regex=True).str.strip()
                 .replace({'פתח תקוה': 'פתח תקווה'}))
    df['value'] = pd.to_numeric(df.value, errors='coerce')
    df = df[df.value.notna()]
    df['year'] = df.year.astype(int)
    df['level'] = df.src.map(geo_level)
    df['population'] = df.src.map(population)
    df['concept'] = df.src.map(concept)
    df['gender'] = df.gender.fillna('סה"כ')
    # the entity a row describes: sub-district tables carry it in geo2, others geo1
    df['entity'] = df.geo1.where(df.level != 'נפה/מחוז', df.geo2.fillna('סה"כ'))
    df['parent'] = df.geo1.where(df.level == 'נפה/מחוז')
    df['ent_n'] = df.entity.map(sanitize)
    df = reconcile_counts(df)

    # ---- Eastern-Galilee tagging ------------------------------------------------
    m = pd.read_excel(MAP)
    auth = m[m['סוג ישות'] == 'רשות'].copy()
    lut = {}
    for _, r in auth.iterrows():
        for nm in {sanitize(r['שם ברשימת אשכול']), sanitize(r['שם רשמי בלמס'])}:
            if nm:
                lut[nm] = (r['שם ברשימת אשכול'], r['קוד למס (סמל)'], r['קבוצה/שיוך'])
    # spelling variants BTL uses that differ from the CBS register
    for a, b in {'קריית שמונה': 'קרית שמונה', 'טובא זנגרייה': 'טובא זנגריה',
                 'מגדל שמס': 'מגדל שמס', 'עין קנייא': 'עין קניה',
                 'בוקעאתא': 'בוקעתא', 'עגר': 'עגר'}.items():
        if b in lut and a not in lut:
            lut[a] = lut[b]
    df['eshkol_name'] = df.ent_n.map(lambda n: lut.get(n, (None,))[0])
    df['eshkol_code'] = df.ent_n.map(lambda n: lut.get(n, (None, None))[1] if n in lut else None)
    df['cluster'] = df.ent_n.map(lambda n: lut.get(n, (None, None, None))[2] if n in lut else None)
    # a name can be an authority at one level and something else at another
    df.loc[(df.level == 'נפה/מחוז'), ['eshkol_name', 'eshkol_code', 'cluster']] = None
    df.loc[(df.level == 'מועצה אזורית') & (~df.entity.isin(
        ['הגליל העליון', 'מבואות החרמון', 'מרום הגליל', 'גולן', 'הגולן',
         'מטה אשר', 'מעלה יוסף'])), ['eshkol_name', 'eshkol_code', 'cluster']] = None

    df.to_pickle('/d/work/master.pkl')
    print('master: %s rows | %d tables | levels %s'
          % (format(len(df), ','), df.src.nunique(), df.level.value_counts().to_dict()))
    print('EG authorities present:', sorted(df[df.cluster == 'גליל מזרחי'].eshkol_name.unique()))


if __name__ == '__main__':
    main()
