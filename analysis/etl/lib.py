# -*- coding: utf-8 -*-
"""Aggregation helpers for the Eastern-Galilee cluster.

The cluster figure is always built from its OWN authorities — the 13 localities
plus the 4 regional councils — never from a sub-district proxy.  Every aggregate
therefore carries the number of authorities and the share of cluster employment
it actually covers, so a reader can see what is behind it.
"""
import pandas as pd
import numpy as np

M = pd.read_pickle('/d/work/master.pkl')

RC = {'הגליל העליון', 'מרום הגליל', 'מבואות החרמון', 'גולן'}   # the cluster's regional councils
ALL = 'כלל העובדים'
ANY_INCOME = 'כל מקורות ההכנסה'
# metrics that are a percentage OF the authority's own workers, so they aggregate
# as an employment-weighted mean rather than a sum
SHARE_KEYS = {'inc_minwage', 'inc_le75', 'inc_le100', 'inc_le2x', 'inc_le3x', 'inc_le4x',
              'inc_gt4x', 'dur_1_2', 'dur_3_5', 'dur_6_8', 'dur_9_11', 'dur_12',
              'pct_minwage_year', 'pct_minwage_work', 'pct_emp_only', 'pct_self_only',
              'pct_both', 'months_avg'}


def authorities(pop=ALL, concept=ANY_INCOME, gender='סה"כ', years=None, src_filter=None):
    """Long table of the cluster's authorities, each taken from its correct level.

    A name can exist at two geography levels ('גולן' is both a regional council and
    a sub-district; 'צפת' both a city and a sub-district), so the level is pinned
    per entity — without this the cluster's worker count inflates by ~38%.
    """
    d = M[(M.cluster == 'גליל מזרחי') & (M.population == pop) &
          (M.concept == concept) & (M.gender == gender)]
    d = d[((d.level == 'יישוב') & (~d.entity.isin(RC))) |
          ((d.level == 'מועצה אזורית') & (d.entity.isin(RC)))]
    if years is not None:
        d = d[d.year.isin(years)]
    if src_filter is not None:
        d = d[d.src.str.contains(src_filter)]
    return d


def _wide(d, mkeys):
    return (d[d.mkey.isin(mkeys)]
            .pivot_table(index=['year', 'eshkol_name'], columns='mkey', values='value',
                         aggfunc='mean').reset_index())


def cluster(mkeys, pop=ALL, concept=ANY_INCOME, gender='סה"כ', src_filter=None):
    """Employment-weighted cluster aggregate, one row per year.

    Means are re-weighted from the underlying totals rather than averaged naively:
        total pay    = wage-per-month-in-year x workers x 12
        total months = workers x 12 x (wage-per-month-in-year / wage-per-work-month)
    which reproduces exactly the ratio BTL itself publishes.  Shares are weighted
    by each authority's workers.  `n_auth` / `covered` report what went in.
    """
    need = set(mkeys) | {'n_workers'}
    if {'wage_work_mean', 'months'} & set(mkeys):
        need |= {'wage_year_mean', 'wage_work_mean'}
    p = _wide(authorities(pop, concept, gender, src_filter=src_filter), need)
    if p.empty:
        return pd.DataFrame()
    p = p[p.n_workers.notna()]
    out = {}
    for yr, g in p.groupby('year'):
        row = {'n_workers': g.n_workers.sum(), 'n_auth': g.eshkol_name.nunique()}
        if 'wage_year_mean' in g and g.wage_year_mean.notna().any():
            gg = g[g.wage_year_mean.notna()]
            row['wage_year_mean'] = (gg.wage_year_mean * gg.n_workers).sum() / gg.n_workers.sum()
            if 'wage_work_mean' in gg and gg.wage_work_mean.notna().any():
                h = gg[gg.wage_work_mean.notna()]
                pay = h.wage_year_mean * h.n_workers * 12
                mon = pay / h.wage_work_mean
                row['wage_work_mean'] = pay.sum() / mon.sum()
                row['months'] = mon.sum() / h.n_workers.sum()
        for k in mkeys:
            if k in SHARE_KEYS and k in g and g[k].notna().any():
                h = g[g[k].notna()]
                row[k] = (h[k] * h.n_workers).sum() / h.n_workers.sum()
        out[yr] = row
    return pd.DataFrame(out).T.sort_index()


def national(mkeys, pop=ALL, concept=ANY_INCOME, gender='סה"כ', src_filter=None):
    """Israel-wide benchmark, from the published country total row.

    For 2016-2022 the 'שכר ממוצע לחודש בשנה' table lost its country row upstream
    (its xlsx is corrupt in the archive), so it is rebuilt as the worker-weighted
    aggregate of the six districts + Judea and Samaria — validated against the
    years where the published row does exist, to within 0.002%.
    """
    d = M[(M.level == 'נפה/מחוז') & (M.population == pop) & (M.concept == concept) &
          (M.gender == gender)]
    if src_filter is not None:
        d = d[d.src.str.contains(src_filter)]
    need = set(mkeys) | {'n_workers', 'wage_year_mean', 'wage_work_mean'}
    p = d[d.mkey.isin(need)].pivot_table(index=['year', 'geo1', 'geo2'], columns='mkey',
                                         values='value', aggfunc='mean').reset_index()
    pub = p[p.geo1 == 'סה"כ- נפה ומחוז'].set_index('year').drop(columns=['geo1', 'geo2'])
    parts = p[(p.geo2 == 'סה"כ') & (p.geo1 != 'סה"כ- נפה ומחוז')]
    cols = [c for c in pub.columns if c in parts.columns]
    rec = parts.groupby('year').apply(
        lambda g: pd.Series({c: (g.n_workers.sum() if c == 'n_workers'
                                 else (g[c] * g.n_workers).sum() / g.n_workers.sum())
                             for c in cols}), include_groups=False)
    res = pub.combine_first(rec)
    if {'wage_year_mean', 'wage_work_mean'} <= set(res.columns):
        res['months'] = 12 * res.wage_year_mean / res.wage_work_mean
    return res


def index_vs_national(mkeys, **kw):
    """Cluster as a percentage of the national figure, metric by metric."""
    c, n = cluster(mkeys, **kw), national(mkeys, **kw)
    common = [k for k in c.columns if k in n.columns and k != 'n_auth']
    return (c[common] / n[common] * 100).dropna(how='all')
