# -*- coding: utf-8 -*-
"""Every result table in analysis/output/ , reproduced in one run.

Geography note: the eshkol's 18 authorities are exactly נפת צפת + נפת גולן —
verified on the CBS 2024 processing, where the 18 authorities sum to 83,774
salaried, the same as the two sub-districts. That lets the sub-district series
(2016-2024, with gender, income groups and work duration) stand in for the
cluster, and the authority-level sum confirms it to within 0.2%.
"""
import os
import numpy as np
import pandas as pd
from lib import M, region, national, eshkol_nafot, authorities, national_localities

OUT = os.path.join(os.path.dirname(__file__), '..', 'output')
REGIONS = ['ארצי', 'תל-אביב', 'המרכז', 'חיפה', 'הצפון', 'הדרום', 'ירושלים', 'נפת צפת', 'נפת גולן']
ALL = 'כלל העובדים'
INC = ['inc_minwage', 'inc_le75', 'inc_le100', 'inc_le2x', 'inc_le3x', 'inc_le4x', 'inc_gt4x']
DUR = ['dur_1_2', 'dur_3_5', 'dur_6_8', 'dur_9_11', 'dur_12', 'months_avg']


def save(df, name):
    df.to_csv(os.path.join(OUT, name), encoding='utf-8-sig')
    return df


def series(nm, mkey, pop=ALL, concept='כל מקורות ההכנסה', gender='סה"כ'):
    d = region(nm)
    d = d[(d.population == pop) & (d.concept == concept) & (d.gender == gender) & (d.mkey == mkey)]
    return d.groupby('year').value.mean()


def wage_tables():
    nat, e = national(), eshkol_nafot()
    for col in ('wage_year_mean', 'wage_work_mean'):
        t = pd.DataFrame({nm: series(nm, col) for nm in REGIONS[1:]})
        t.insert(0, 'ארצי', nat[col])
        t['אשכול גליל מזרחי'] = e[col]
        save(t.round(0), 'wage_%s.csv' % col)
        save((t.div(t['ארצי'], axis=0) * 100).round(1), 'idx_%s.csv' % col)
    return nat, e


def volumes(nat, e):
    N = pd.DataFrame({nm: series(nm, 'n_workers') for nm in ['תל-אביב', 'הצפון', 'נפת צפת', 'נפת גולן']})
    N.insert(0, 'ארצי', nat.n_workers)
    N['אשכול'] = e.n_workers
    save(N, 'workers.csv')
    # months worked, derived as 12 x (pay per month-in-year) / (pay per work-month)
    Mo = pd.DataFrame({nm: 12 * series(nm, 'wage_year_mean') / series(nm, 'wage_work_mean')
                       for nm in REGIONS[1:]})
    Mo.insert(0, 'ארצי', 12 * nat.wage_year_mean / nat.wage_work_mean)
    Mo['אשכול'] = e.months
    save(Mo.round(2), 'months.csv')


def distributions():
    rows = {}
    for nm in REGIONS:
        d = region(nm)
        d = d[(d.population == ALL) & (d.gender == 'סה"כ') & (d.year == 2024) &
              (d.mkey.isin(INC)) & (d.src.str.contains('לחודש עבודה'))]
        rows[nm] = d.groupby('mkey').value.mean()
    I = pd.DataFrame(rows).T[INC]
    I.columns = ['עד שכר מינימום', 'עד 75% מהממוצע', 'עד הממוצע', 'עד פי 2', 'עד פי 3', 'עד פי 4', 'מעל פי 4']
    save(I.round(1), 'income_dist2024.csv')

    rows = {}
    for nm in REGIONS:
        d = region(nm)
        d = d[(d.population == ALL) & (d.gender == 'סה"כ') & (d.year == 2024) & (d.mkey.isin(DUR))]
        rows[nm] = d.groupby('mkey').value.mean()
    D = pd.DataFrame(rows).T[DUR]
    D.columns = ['1-2 חוד׳', '3-5 חוד׳', '6-8 חוד׳', '9-11 חוד׳', '12 חוד׳', 'ממוצע חוד׳']
    save(D.round(2), 'duration2024.csv')


def gender():
    rows = []
    for nm in REGIONS:
        d = region(nm)
        d = d[(d.population == ALL) & (d.concept == 'כל מקורות ההכנסה') & (d.year == 2024)]
        g = d.pivot_table(index='gender', columns='mkey', values='value', aggfunc='mean')
        if not {'גברים', 'נשים'} <= set(g.index):
            continue
        for col, lab in [('wage_work_mean', 'לחודש עבודה'), ('wage_year_mean', 'לחודש בשנה')]:
            rows.append(dict(אזור=nm, בסיס=lab, גברים=g.loc['גברים', col], נשים=g.loc['נשים', col],
                             יחס=100 * g.loc['נשים', col] / g.loc['גברים', col],
                             חלק_נשים=100 * g.loc['נשים', 'n_workers'] /
                                       (g.loc['נשים', 'n_workers'] + g.loc['גברים', 'n_workers'])))
    pd.DataFrame(rows).round(1).to_csv(os.path.join(OUT, 'gender2024.csv'),
                                       index=False, encoding='utf-8-sig')
    # trend from the locality x gender family
    gl = M[M.src.str.contains('לפי מגדר ולפי יישוב') & M.mkey.isin(['wage_work_mean', 'n_workers'])]
    q = (gl[gl.cluster == 'גליל מזרחי']
         .pivot_table(index=['year', 'eshkol_name', 'gender'], columns='mkey', values='value').reset_index())
    gg = q.groupby(['year', 'gender']).apply(
        lambda g: (g.wage_work_mean * g.n_workers).sum() / g.n_workers.sum(), include_groups=False).unstack()
    gg['יחס_נ/ג'] = 100 * gg['נשים'] / gg['גברים']
    ng = (gl[gl.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
          .pivot_table(index='year', columns='gender', values='value', aggfunc='mean'))
    save(gg.round(1), 'gender_trend.csv')


def local_tables():
    save(authorities(2024).round(1).set_index('eshkol_name'), 'authorities2024.csv')
    fam = M[M.src.str.match(r'שכר ממוצע וחציוני, חודשי ושנתי של כלל העובדים, לפי יישוב, 20\d\d')]
    loc = fam[(fam.gender == 'סה"כ') & fam.mkey.isin(['wage_work_mean', 'wage_work_med', 'n_workers'])]
    p = (loc[loc.cluster == 'גליל מזרחי']
         .pivot_table(index=['year', 'eshkol_name'], columns='mkey', values='value').reset_index())
    agg = p.groupby('year').apply(lambda g: pd.Series({
        'מועסקים': g.n_workers.sum(),
        'ממוצע': (g.wage_work_mean * g.n_workers).sum() / g.n_workers.sum(),
        'חציון': g.wage_work_med.median()}), include_groups=False)
    nat = (loc[loc.entity.astype(str).str.contains('סך הכל', na=False)]
           .pivot_table(index='year', columns='mkey', values='value', aggfunc='mean'))
    t = agg.join(nat[['wage_work_mean', 'wage_work_med']]
                 .rename(columns={'wage_work_mean': 'ארצי_ממוצע', 'wage_work_med': 'ארצי_חציון'}))
    t['מדד_ממוצע'] = 100 * t['ממוצע'] / t.ארצי_ממוצע
    t['מדד_חציון'] = 100 * t['חציון'] / t.ארצי_חציון
    save(t.round(1), 'median_trend.csv')
    mw = M[(M.mkey == 'pct_minwage_work') & (M.level == 'יישוב')]
    eg = mw[mw.cluster == 'גליל מזרחי'].pivot_table(index='eshkol_name', columns='year',
                                                    values='value', aggfunc='mean')
    eg.loc['— כלל יישובי הארץ —'] = (mw[mw.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
                                     .groupby('year').value.mean())
    save(eg.round(1), 'minwage_pct.csv')


def shift_share():
    """Split the Safed+Golan wage gap into industry mix vs pay within industry."""
    F = os.path.join(os.path.dirname(__file__), '..', '..', 'עיבוד לפי ענף ורשות בני דורמבט.xlsx')
    b = pd.read_excel(F, 'לפי ענף כלכלי', header=None).iloc[3:, 1:8]
    b.columns = ['anaf', 'n_nat', 'mon_nat', 'w_nat', 'n_eg', 'mon_eg', 'w_eg']
    for c in b.columns[1:]:
        b[c] = pd.to_numeric(b[c], errors='coerce')
    b = b[b.anaf.notna()]
    dic = pd.read_excel(os.path.join(os.path.dirname(__file__), '..', '..',
                                     'dicAnaf4SfarotMaster 2.xlsx'), 'רשימת הערכים במילון ענפי כלכלה')
    lut = dict(zip(dic.SemelAnaf2Sfarot.dropna().astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(2),
                   dic.ShemAnaf2Sfarot))
    def label(code):
        parts = [p.strip().zfill(2) for p in str(code).replace('.0', '').split('+')]
        names = [lut[p] for p in parts if p in lut]
        return (names[0] + (' +' if len(parts) > 1 else '')) if names else str(code)
    b['ענף'] = b.anaf.map(label)
    d = b.dropna(subset=['n_eg', 'w_eg', 'w_nat']).copy()
    d['s_nat'] = d.n_nat / d.n_nat.sum()
    d['s_eg'] = d.n_eg / d.n_eg.sum()
    d['c_mix'] = (d.s_eg - d.s_nat) * d.w_nat        # different industries, national pay
    d['c_pay'] = d.s_nat * (d.w_eg - d.w_nat)        # same industries, local pay
    d['w_ratio'] = 100 * d.w_eg / d.w_nat
    d.to_csv(os.path.join(OUT, 'shiftshare.csv'), index=False, encoding='utf-8-sig')
    W_nat, W_eg = (d.s_nat * d.w_nat).sum(), (d.s_eg * d.w_eg).sum()
    print('  ארצי %.0f | אשכול %.0f (%.1f%%) | הרכב %.0f | שכר בתוך ענף %.0f'
          % (W_nat, W_eg, 100 * W_eg / W_nat, d.c_mix.sum(), d.c_pay.sum()))
    print('  תרחיש הרכב ענפי ארצי: %.0f | תרחיש שכר ארצי בכל ענף: %.0f'
          % ((d.s_nat * d.w_eg).sum(), (d.s_eg * d.w_nat).sum()))


if __name__ == '__main__':
    nat, e = wage_tables()
    volumes(nat, e)
    distributions()
    gender()
    local_tables()
    shift_share()
    print('wrote', len(os.listdir(OUT)), 'tables to', os.path.abspath(OUT))
