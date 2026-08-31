# -*- coding: utf-8 -*-
"""Shared helpers for the Eastern-Galilee wage analysis."""
import pandas as pd, numpy as np

M = pd.read_pickle('/d/work/master.pkl')
RC = {'הגליל העליון', 'מרום הגליל', 'מבואות החרמון', 'גולן'}   # eshkol regional councils
EG_NAFOT = ['צפת', 'גולן']          # the eshkol == נפת צפת + נפת גולן (verified on CBS 2024)


def region(name):
    """Pull one comparison region out of the district/sub-district tables."""
    d = M[M.level == 'נפה/מחוז']
    if name == 'ארצי':
        return d[d.geo1 == 'סה"כ- נפה ומחוז']
    if name in ('נפת צפת', 'נפת גולן'):
        return d[(d.geo1 == 'הצפון') & (d.geo2 == name.replace('נפת ', ''))]
    return d[(d.geo1 == name) & (d.geo2 == 'סה"כ')]


def wide(df, keys=('year', 'gender')):
    return df.pivot_table(index=list(keys), columns='mkey', values='value', aggfunc='mean')


def eshkol_nafot(pop='כלל העובדים', concept='כל מקורות ההכנסה', gender='סה"כ'):
    """Aggregate נפת צפת + נפת גולן into one eshkol series.

    Means are re-weighted from the underlying totals, never averaged naively:
      total pay  = wage-per-month-in-year x workers x 12
      total months worked = workers x 12 x (wage-per-month-in-year / wage-per-work-month)
    so the eshkol figure is a true aggregate ratio, exactly as BTL computes its own.
    """
    d = M[(M.level == 'נפה/מחוז') & (M.geo1 == 'הצפון') & (M.geo2.isin(EG_NAFOT)) &
          (M.population == pop) & (M.concept == concept) & (M.gender == gender)]
    p = d.pivot_table(index=['year', 'geo2'], columns='mkey', values='value', aggfunc='mean').reset_index()
    if 'n_workers' not in p or 'wage_year_mean' not in p:
        return pd.DataFrame()
    p['pay'] = p.wage_year_mean * p.n_workers * 12
    p['mon'] = p.n_workers * 12 * p.wage_year_mean / p.wage_work_mean
    g = p.groupby('year').agg(n_workers=('n_workers', 'sum'), pay=('pay', 'sum'), mon=('mon', 'sum'))
    g['wage_year_mean'] = g.pay / (g.n_workers * 12)
    g['wage_work_mean'] = g.pay / g.mon
    g['months'] = g.mon / g.n_workers
    return g.drop(columns=['pay', 'mon'])


def authorities(year, pop='כלל העובדים', concept='כל מקורות ההכנסה', gender='סה"כ', mkeys=None):
    """The eshkol's authorities, taking each from its correct geography level.

    A name can exist at two levels (סמל 26 'ראש פינה' the locality vs a regional
    council; 'גולן' the RC vs the sub-district), so the level is pinned per entity.
    """
    mkeys = mkeys or ['wage_year_mean', 'wage_work_mean', 'wage_year_med',
                      'wage_work_med', 'n_workers', 'months_avg']
    d = M[(M.year == year) & (M.gender == gender) & (M.population == pop) &
          (M.concept == concept) & (M.cluster == 'גליל מזרחי') & (M.mkey.isin(mkeys))]
    d = d[((d.level == 'יישוב') & (~d.entity.isin(RC))) |
          ((d.level == 'מועצה אזורית') & (d.entity.isin(RC)))]
    return d.pivot_table(index=['eshkol_name', 'level'], columns='mkey',
                         values='value', aggfunc='mean').reset_index()


def national_localities(year, mkey, pop='כלל העובדים', concept='כל מקורות ההכנסה', gender='סה"כ'):
    """All localities+RCs nationally for that metric — the ranking universe."""
    d = M[(M.year == year) & (M.gender == gender) & (M.population == pop) &
          (M.concept == concept) & (M.mkey == mkey) & (M.level.isin(['יישוב', 'מועצה אזורית']))]
    d = d[~d.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
    return d.groupby(['entity', 'level'], as_index=False).value.mean()


def national(pop='כלל העובדים', concept='כל מקורות ההכנסה', gender='סה"כ'):
    """National series. 2023-24 come straight from the published total row; for
    2016-2022 the 'שכר ממוצע לחודש בשנה' table lost its total row upstream (its
    xlsx is corrupt in the archive), so the total is rebuilt as the worker-weighted
    aggregate of the seven districts — exact for counts, and exact by construction
    for wage-per-month-in-year, which is itself total pay / (workers x 12)."""
    d = M[(M.level == 'נפה/מחוז') & (M.population == pop) & (M.concept == concept) &
          (M.gender == gender)]
    p = d.pivot_table(index=['year', 'geo1', 'geo2'], columns='mkey', values='value',
                      aggfunc='mean').reset_index()
    pub = p[p.geo1 == 'סה"כ- נפה ומחוז'].set_index('year')
    parts = p[(p.geo2 == 'סה"כ') & (p.geo1 != 'סה"כ- נפה ומחוז')]
    cols = [c for c in ('wage_year_mean', 'wage_work_mean', 'n_workers') if c in parts]
    rec = parts.groupby('year').apply(
        lambda g: pd.Series({c: (g[c] * g.n_workers).sum() / g.n_workers.sum()
                             if c != 'n_workers' else g.n_workers.sum() for c in cols}),
        include_groups=False)
    return pub.reindex(columns=[c for c in pub.columns if c in cols]).combine_first(rec)
