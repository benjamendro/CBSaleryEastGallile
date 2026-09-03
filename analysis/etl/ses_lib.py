# -*- coding: utf-8 -*-
"""Socio-economic peer comparison.

The CBS 'רשויות מקומיות' publication (p_libud_24.xlsx) ranks every municipal
authority into a socio-economic cluster, 1 (lowest) to 10.  Comparing a cluster
authority to the national average of authorities in *its own* socio-economic
cluster answers a question the wage data alone cannot: is the wage here low
because the place is disadvantaged, or low even for a place like this?

Caveats that must travel with every number produced here:
  * the socio-economic index is for 2021, the wage data for 2024;
  * the index itself is built partly from income and employment variables, so it
    is not independent of wages.  That makes a gap against socio-economic peers
    conservative — the index has already absorbed part of the low income;
  * the index measures household income from all sources (including transfers,
    pensions and capital) among residents, while the wage index measures wage per
    month worked among workers.  A place can score well on one and poorly on the
    other.
  * only municipal authorities carry an index.  Of the 341 authorities the BTL
    tables publish, 253 match a socio-economic row; the rest are localities
    inside regional councils, which have no index of their own.
"""
import os, re
import pandas as pd, numpy as np

ROOT = os.environ.get('EG_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
F = os.path.join(ROOT, 'p_libud_24.xlsx')
SHEET = 'נתונים פיזיים ונתוני אוכלוסייה '
COL = {'name': 0, 'code': 1, 'status': 3, 'pop': 12, 'ses_cluster': 250, 'ses_value': 251, 'ses_rank': 252}

CLUSTER = {'צפת', 'קריית שמונה', 'חצור הגלילית', 'ראש פינה', 'מטולה', "ג'ש (גוש חלב)",
           'טובא-זנגרייה', 'בוקעאתא', "מג'דל שמס", 'מסעדה', "ע'ג'ר", 'עין קנייא', 'קצרין',
           'גולן', 'הגליל העליון', 'מרום הגליל', 'מבואות החרמון'}


def norm(s):
    """One spelling for the same authority across CBS and BTL files."""
    s = str(s).strip().replace('־', '-').replace('–', '-')
    s = re.sub(r"[’'`׳]", "'", s)
    s = re.sub(r'[״"”]', '"', s)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'^ה(?=[א-ת])', '', s)          # 'הגליל העליון' == 'גליל עליון'
    return (s.replace('קרית', 'קריית').replace('טובא-זנגריה', 'טובא-זנגרייה')
             .replace('(', '').replace(')', ''))


def ses_table():
    d = pd.read_excel(F, SHEET, header=None)
    t = d.iloc[4:, list(COL.values())].copy()
    t.columns = list(COL)
    for c in ('code', 'pop', 'ses_cluster', 'ses_value', 'ses_rank'):
        t[c] = pd.to_numeric(t[c], errors='coerce')
    t = t[t.name.notna() & t.code.notna()].copy()
    t['name'] = t.name.astype(str).str.strip()
    t['k'] = t.name.map(norm)
    return t[t.ses_cluster.notna()]


def national_profile(master):
    """One row per authority the BTL tables publish, 2024 profile plus 2023->2024 change."""
    KEYS = ['wage_work_mean', 'wage_work_med', 'n_workers', 'inc_minwage',
            'inc_le3x', 'inc_le4x', 'inc_gt4x', 'dur_12']
    base = master[(master.year.isin([2023, 2024])) & (master.population == 'כלל העובדים') &
                  (master.concept == 'כל מקורות ההכנסה') &
                  master.level.isin(['יישוב', 'מועצה אזורית']) & master.mkey.isin(KEYS)]
    base = base[~base.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
    tot = base[base.gender == 'סה"כ'].pivot_table(
        index=['level', 'entity'], columns=['mkey', 'year'], values='value', aggfunc='mean')
    g = master[(master.year == 2024) & (master.population == 'כלל העובדים') &
               (master.concept == 'כל מקורות ההכנסה') &
               master.level.isin(['יישוב', 'מועצה אזורית']) &
               master.mkey.isin(['wage_work_mean', 'n_workers']) &
               master.gender.isin(['גברים', 'נשים'])]
    g = g[~g.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
    gp = g.pivot_table(index=['level', 'entity'], columns=['mkey', 'gender'], values='value', aggfunc='mean')
    NAT = 14751.0                      # national mean wage per month worked, 2024
    r = pd.DataFrame(index=tot.index)
    r['n'] = tot[('n_workers', 2024)]
    r['idx'] = 100 * tot[('wage_work_mean', 2024)] / NAT
    r['mm'] = 100 * tot[('wage_work_med', 2024)] / tot[('wage_work_mean', 2024)]
    r['minw'] = tot[('inc_minwage', 2024)]
    r['top'] = tot[('inc_le3x', 2024)] + tot[('inc_le4x', 2024)] + tot[('inc_gt4x', 2024)]
    r['d12'] = tot[('dur_12', 2024)]
    r['dN'] = 100 * (tot[('n_workers', 2024)] / tot[('n_workers', 2023)] - 1)
    r['gr'] = 100 * gp[('wage_work_mean', 'נשים')] / gp[('wage_work_mean', 'גברים')]
    r['fs'] = 100 * gp[('n_workers', 'נשים')] / (gp[('n_workers', 'נשים')] + gp[('n_workers', 'גברים')])
    return r.reset_index()


def pool(master):
    """The comparison pool: authorities that have both a wage profile and an index."""
    r = national_profile(master)
    r['k'] = r.entity.map(norm)
    s = ses_table()
    d = r.merge(s[['k', 'code', 'status', 'ses_cluster', 'ses_value', 'ses_rank']], on='k', how='inner')
    d['in_cluster'] = d.k.isin({norm(x) for x in CLUSTER})
    return d


METRICS = ['idx', 'minw', 'top', 'mm', 'gr', 'fs', 'd12', 'dN']


def compare(d, metrics=METRICS, exclude_own=True):
    """Each cluster authority against the mean of its socio-economic peers."""
    rows = []
    for _, a in d[d.in_cluster].iterrows():
        peers = d[d.ses_cluster == a.ses_cluster]
        peers = peers[~peers.in_cluster] if exclude_own else peers[peers.entity != a.entity]
        row = {'entity': a.entity, 'status': a.status, 'ses': int(a.ses_cluster),
               'n': int(a.n), 'peers': len(peers)}
        for m in metrics:
            row[m] = a[m]
            row[m + '_p'] = peers[m].mean()
            row['d_' + m] = a[m] - peers[m].mean()
        rows.append(row)
    return pd.DataFrame(rows).sort_values('d_idx')
