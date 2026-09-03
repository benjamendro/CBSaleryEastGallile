# -*- coding: utf-8 -*-
"""All result tables for the Eastern-Galilee wage analysis, in one run.

Two sources are used and never mixed in a single comparison:
  BTL  - National Insurance Institute locality / regional-council tables, 2016-2024.
  CBS  - the special processing by industry, 2024, salaried only.
They agree on head counts and months worked but differ ~14% on the wage level
because BTL publishes an aggregate ratio and the CBS an average per person, so
each source is only ever compared against its own national benchmark.
"""
import os
import numpy as np
import pandas as pd
from lib import M, RC, cluster, national, authorities, index_vs_national

OUT = os.path.join(os.path.dirname(__file__), '..', 'output')
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
INC = ['inc_minwage', 'inc_le75', 'inc_le100', 'inc_le2x', 'inc_le3x', 'inc_le4x', 'inc_gt4x']
INC_HE = ['עד שכר המינימום', 'מינימום – 75% מהממוצע', '75%–100% מהממוצע',
          'פי 1–2 מהממוצע', 'פי 2–3', 'פי 3–4', 'מעל פי 4']
DUR = ['dur_1_2', 'dur_3_5', 'dur_6_8', 'dur_9_11', 'dur_12', 'months_avg']
DUR_HE = ['1-2 חודשים', '3-5 חודשים', '6-8 חודשים', '9-11 חודשים', '12 חודשים', 'ממוצע חודשים']
NAT24 = {'mean': 14751.0, 'med': 10401.0}


def save(df, name):
    df.to_csv(os.path.join(OUT, name), encoding='utf-8-sig')
    return df


def region(name):
    """A comparison region, from the published district tables."""
    d = M[M.level == 'נפה/מחוז']
    return d[(d.geo1 == name) & (d.geo2 == 'סה"כ')]


def region_series(name, mkey, pop='כלל העובדים'):
    d = region(name)
    d = d[(d.population == pop) & (d.concept == 'כל מקורות ההכנסה') &
          (d.gender == 'סה"כ') & (d.mkey == mkey)]
    return d.groupby('year').value.mean()


# ---------------------------------------------------------------- 1. wage level
def wage_level():
    c = cluster(['wage_year_mean', 'wage_work_mean'])
    n = national(['wage_year_mean', 'wage_work_mean'])
    for col in ('wage_year_mean', 'wage_work_mean'):
        t = pd.DataFrame({'ארצי': n[col], 'תל־אביב': region_series('תל-אביב', col),
                          'המרכז': region_series('המרכז', col), 'חיפה': region_series('חיפה', col),
                          'הצפון': region_series('הצפון', col), 'הדרום': region_series('הדרום', col),
                          'ירושלים': region_series('ירושלים', col), 'אשכול גליל מזרחי': c[col]})
        save(t.round(0), 'wage_%s.csv' % col)
        save((t.div(t['ארצי'], axis=0) * 100).round(1), 'idx_%s.csv' % col)
    save(c.round(1), 'cluster_series.csv')
    return c, n


# ------------------------------------------------------------ 2. volume & hours
def volumes(c, n):
    N = pd.DataFrame({'ארצי': n.n_workers, 'תל־אביב': region_series('תל-אביב', 'n_workers'),
                      'הצפון': region_series('הצפון', 'n_workers'), 'אשכול': c.n_workers})
    save(N, 'workers.csv')
    save((N.pct_change() * 100).round(1), 'workers_yoy.csv')
    Mo = pd.DataFrame({'ארצי': n.months, 'אשכול': c.months,
                       'תל־אביב': 12 * region_series('תל-אביב', 'wage_year_mean') /
                                  region_series('תל-אביב', 'wage_work_mean')})
    save(Mo.round(2), 'months.csv')
    d = cluster(DUR)
    nd = national(DUR)
    t = pd.DataFrame({'אשכול': d.loc[2024, DUR].values, 'ארצי': nd.loc[2024, DUR].values,
                      'תל־אביב': [region(  'תל-אביב')[(region('תל-אביב').mkey == k) &
                                  (region('תל-אביב').year == 2024) &
                                  (region('תל-אביב').population == 'כלל העובדים') &
                                  (region('תל-אביב').gender == 'סה"כ')].value.mean() for k in DUR]},
                     index=DUR_HE)
    save(t.round(2), 'duration2024.csv')


# ---------------------------------------------------------- 3. income spread
def spread():
    c = cluster(INC, src_filter='לחודש עבודה')
    n = national(INC, src_filter='לחודש עבודה')
    t = pd.DataFrame({'אשכול 2023': c.loc[2023, INC].values, 'ארצי 2023': n.loc[2023, INC].values,
                      'אשכול 2024': c.loc[2024, INC].values, 'ארצי 2024': n.loc[2024, INC].values},
                     index=INC_HE)
    save(t.round(1), 'income_dist.csv')

    a = authorities(years=[2024])
    p = a[a.mkey.isin(['wage_work_mean', 'wage_work_med', 'n_workers'])].pivot_table(
        index='eshkol_name', columns='mkey', values='value', aggfunc='mean')
    p['מדד_ממוצע'] = 100 * p.wage_work_mean / NAT24['mean']
    p['מדד_חציון'] = 100 * p.wage_work_med / NAT24['med']
    p['חציון_חלקי_ממוצע'] = 100 * p.wage_work_med / p.wage_work_mean
    # national ranking universe: localities of 2,000+ residents plus regional councils
    u = M[(M.year == 2024) & (M.gender == 'סה"כ') & (M.population == 'כלל העובדים') &
          (M.concept == 'כל מקורות ההכנסה') & (M.mkey == 'wage_work_mean') &
          (M.level.isin(['יישוב', 'מועצה אזורית']))]
    u = u[~u.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
    uni = u.groupby(['level', 'entity']).value.mean()
    p['מקום_ארצי'] = p.wage_work_mean.map(lambda v: int((uni > v).sum() + 1))
    p['מתוך'] = len(uni)
    save(p.sort_values('wage_work_mean', ascending=False).round(1), 'authorities2024.csv')
    return p


# ------------------------------------------------------------------ 4. gender
def gender():
    """Gender is reported on two different table families, so the series breaks.

    2016-2022 exists only in 'לפי מגדר ולפי יישוב' — the 12 cluster localities, no
    regional councils — and its national benchmark is 'all localities of 2,000+
    residents', not the whole country.  2023-2024 covers all 17 authorities and is
    comparable to the national total.  The two blocks are written separately and
    must not be read as one continuous line.
    """
    early = M[M.src.str.contains('לפי מגדר ולפי יישוב') &
              M.mkey.isin(['wage_work_mean', 'n_workers'])]
    eg = (early[early.cluster == 'גליל מזרחי']
          .pivot_table(index=['year', 'eshkol_name', 'gender'], columns='mkey', values='value')
          .reset_index())
    w = eg.groupby(['year', 'gender']).apply(
        lambda g: pd.Series({'wage': (g.wage_work_mean * g.n_workers).sum() / g.n_workers.sum(),
                             'n': g.n_workers.sum(), 'auth': g.eshkol_name.nunique()}),
        include_groups=False).unstack()
    nat = (early[early.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
           .pivot_table(index=['year', 'gender'], columns='mkey', values='value', aggfunc='mean')
           .unstack())
    a = pd.DataFrame({'אשכול_גברים': w[('wage', 'גברים')], 'אשכול_נשים': w[('wage', 'נשים')],
                      'ארצי_גברים': nat[('wage_work_mean', 'גברים')],
                      'ארצי_נשים': nat[('wage_work_mean', 'נשים')],
                      'n_אשכול_גברים': w[('n', 'גברים')], 'n_אשכול_נשים': w[('n', 'נשים')],
                      'רשויות': w[('auth', 'גברים')]})
    a['בסיס'] = 'יישובי האשכול בלבד · ארצי = יישובים 2,000+'

    late = {}
    for gs in ('גברים', 'נשים'):
        c, n = cluster(['wage_work_mean'], gender=gs), national(['wage_work_mean'], gender=gs)
        late['אשכול_' + gs] = c.wage_work_mean
        late['ארצי_' + gs] = n.wage_work_mean
        late['n_אשכול_' + gs] = c.n_workers
        late['רשויות'] = c.n_auth
    b = pd.DataFrame(late).loc[[2023, 2024]]
    b['בסיס'] = 'כל רשויות האשכול · ארצי = כלל המשק'

    g = pd.concat([a, b])
    g['יחס_אשכול'] = 100 * g['אשכול_נשים'] / g['אשכול_גברים']
    g['יחס_ארצי'] = 100 * g['ארצי_נשים'] / g['ארצי_גברים']
    g['שיעור_נשים_אשכול'] = 100 * g['n_אשכול_נשים'] / (g['n_אשכול_נשים'] + g['n_אשכול_גברים'])
    save(g.round(1), 'gender.csv')


# ------------------------------------------------------- 5. low pay & structure
def low_pay():
    mw = M[(M.mkey == 'pct_minwage_work') & (M.level == 'יישוב')]
    eg = mw[mw.cluster == 'גליל מזרחי'].pivot_table(index='eshkol_name', columns='year',
                                                    values='value', aggfunc='mean')
    eg.loc['— כלל יישובי הארץ —'] = (mw[mw.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
                                     .groupby('year').value.mean())
    save(eg.round(1), 'minwage_pct.csv')
    st = M[M.mkey.isin(['pct_emp_only', 'pct_self_only', 'pct_both']) &
           (M.level == 'מועצה אזורית')]
    egs = st[st.cluster == 'גליל מזרחי'].pivot_table(index=['eshkol_name', 'year'], columns='mkey',
                                                     values='value', aggfunc='mean')
    nat = (st[st.entity.astype(str).str.contains('סה"כ', na=False)]
           .pivot_table(index='year', columns='mkey', values='value', aggfunc='mean'))
    nat.index = pd.MultiIndex.from_product([['— כלל המועצות האזוריות —'], nat.index])
    save(pd.concat([egs, nat]).round(1), 'selfemployed.csv')


# --------------------------------------------------------------- 6. shift-share
def shift_share():
    b = pd.read_excel(os.path.join(ROOT, 'עיבוד לפי ענף ורשות בני דורמבט.xlsx'),
                      'לפי ענף כלכלי', header=None).iloc[3:, 1:8]
    b.columns = ['anaf', 'n_nat', 'mon_nat', 'w_nat', 'n_eg', 'mon_eg', 'w_eg']
    for c in b.columns[1:]:
        b[c] = pd.to_numeric(b[c], errors='coerce')
    dic = pd.read_excel(os.path.join(ROOT, 'dicAnaf4SfarotMaster 2.xlsx'),
                        'רשימת הערכים במילון ענפי כלכלה')
    lut = dict(zip(dic.SemelAnaf2Sfarot.dropna().astype(str)
                   .str.replace(r'\.0$', '', regex=True).str.zfill(2), dic.ShemAnaf2Sfarot))
    def label(code):
        parts = [p.strip().zfill(2) for p in str(code).replace('.0', '').split('+')]
        names = [lut[p] for p in parts if p in lut]
        return (names[0] + (' +' if len(parts) > 1 else '')) if names else str(code)
    d = b[b.anaf.notna()].dropna(subset=['n_eg', 'w_eg', 'w_nat']).copy()
    d['ענף'] = d.anaf.map(label)
    d['s_nat'] = d.n_nat / d.n_nat.sum()
    d['s_eg'] = d.n_eg / d.n_eg.sum()
    # symmetric split: mix priced at the average wage, pay weighted by the average
    # share, so the two terms add up to the gap exactly with no residual to explain
    d['c_mix'] = (d.s_eg - d.s_nat) * ((d.w_eg + d.w_nat) / 2)
    d['c_pay'] = ((d.s_eg + d.s_nat) / 2) * (d.w_eg - d.w_nat)
    d['tot'] = d.c_mix + d.c_pay
    d['w_ratio'] = 100 * d.w_eg / d.w_nat
    d.to_csv(os.path.join(OUT, 'shiftshare.csv'), index=False, encoding='utf-8-sig')
    W_nat, W_eg = (d.s_nat * d.w_nat).sum(), (d.s_eg * d.w_eg).sum()
    gap = W_eg - W_nat
    print('  CBS 2024 salaried: national %.0f | cluster %.0f (%.1f%%)' % (W_nat, W_eg, 100 * W_eg / W_nat))
    print('  mix %.0f (%.0f%%) | pay %.0f (%.0f%%) | residual %.9f'
          % (d.c_mix.sum(), 100 * d.c_mix.sum() / gap, d.c_pay.sum(),
             100 * d.c_pay.sum() / gap, gap - d.tot.sum()))
    print('  counterfactuals: national mix %.0f | national pay %.0f'
          % ((d.s_nat * d.w_eg).sum(), (d.s_eg * d.w_nat).sum()))
    print('  coverage: %.1f%% of national salaried, %.1f%% of cluster salaried'
          % (100 * d.n_nat.sum() / 4418600, 100 * d.n_eg.sum() / 83774))
    return d


# ------------------------------------------------------- 7. per-authority profile
def authority_profile():
    """One row per authority across every dimension the source supports."""
    from scipy import stats
    ALLP, ANY = ['כלל העובדים'], ['כל מקורות ההכנסה']

    def piv(pop, con, keys, years, gender='סה"כ'):
        d = M[(M.cluster == 'גליל מזרחי') & M.population.isin(pop) & M.concept.isin(con) &
              (M.gender == gender) & M.mkey.isin(keys) & M.year.isin(years)]
        d = d[((d.level == 'יישוב') & (~d.entity.isin(RC))) |
              ((d.level == 'מועצה אזורית') & (d.entity.isin(RC)))]
        return d.pivot_table(index='eshkol_name', columns=['mkey', 'year'], values='value', aggfunc='mean')

    c = piv(ALLP, ANY, ['n_workers', 'wage_work_mean', 'wage_work_med', 'months_avg', 'dur_12',
                        'dur_1_2', 'inc_minwage', 'inc_le3x', 'inc_le4x', 'inc_gt4x'],
            [2016, 2022, 2023, 2024])
    P = pd.DataFrame(index=c.index)
    P['מועסקים'] = c[('n_workers', 2024)]
    P['שכר_ממוצע'] = c[('wage_work_mean', 2024)]
    P['שכר_חציוני'] = c[('wage_work_med', 2024)]
    P['מדד_ממוצע'] = 100 * c[('wage_work_mean', 2024)] / NAT24['mean']
    P['מדד_חציון'] = 100 * c[('wage_work_med', 2024)] / NAT24['med']
    P['חציון_חלקי_ממוצע'] = 100 * c[('wage_work_med', 2024)] / c[('wage_work_mean', 2024)]
    P['עד_שכר_מינימום'] = c[('inc_minwage', 2024)]
    P['מעל_פי2_מהממוצע'] = c[('inc_le3x', 2024)] + c[('inc_le4x', 2024)] + c[('inc_gt4x', 2024)]
    P['שעבדו_12_חודשים'] = c[('dur_12', 2024)]
    P['עבדו_1-2_חודשים'] = c[('dur_1_2', 2024)]
    for g in ('גברים', 'נשים'):
        gg = piv(ALLP, ANY, ['wage_work_mean', 'n_workers'], [2023, 2024], gender=g)
        P['שכר_' + g] = gg[('wage_work_mean', 2024)]
        P['n_' + g] = gg[('n_workers', 2024)]
        P['שינוי_' + g] = 100 * (gg[('n_workers', 2024)] / gg[('n_workers', 2023)] - 1)
    P['יחס_מגדרי'] = 100 * P['שכר_נשים'] / P['שכר_גברים']
    P['שיעור_נשים'] = 100 * P['n_נשים'] / (P['n_נשים'] + P['n_גברים'])
    e = piv(['שכירים'], ['מעבודה שכירה בלבד'], ['wage_work_mean', 'n_workers'], [2024])
    s = piv(['עצמאים'], ['מעבודה עצמאית בלבד'], ['wage_work_mean', 'n_workers'], [2024])
    P['שיעור_עצמאים'] = 100 * s[('n_workers', 2024)] / P['מועסקים']
    P['יחס_עצמאי_לשכיר'] = 100 * s[('wage_work_mean', 2024)] / e[('wage_work_mean', 2024)]
    P['שינוי_מועסקים_23_24'] = 100 * (c[('n_workers', 2024)] / c[('n_workers', 2023)] - 1)
    P['שינוי_שכר_23_24'] = 100 * (c[('wage_work_mean', 2024)] / c[('wage_work_mean', 2023)] - 1)
    P['שינוי_חציון_23_24'] = 100 * (c[('wage_work_med', 2024)] / c[('wage_work_med', 2023)] - 1)
    P['צמיחת_שכר_16_24'] = 100 * (c[('wage_work_mean', 2024)] / c[('wage_work_mean', 2016)] - 1)
    u = M[(M.year == 2024) & (M.gender == 'סה"כ') & (M.population == 'כלל העובדים') &
          (M.concept == 'כל מקורות ההכנסה') & (M.mkey == 'wage_work_mean') &
          M.level.isin(['יישוב', 'מועצה אזורית'])]
    u = u[~u.entity.astype(str).str.contains('סה"כ|סך הכל', na=False)]
    uni = u.groupby(['level', 'entity']).value.mean()
    P['מקום_ארצי'] = P.שכר_ממוצע.map(lambda v: int((uni > v).sum() + 1))
    save(P.sort_values('מדד_ממוצע', ascending=False).round(1), 'authority_profile.csv')

    # the 2024 wage rise is a composition effect: where employment fell, pay rose
    x, y, ym = P.שינוי_מועסקים_23_24, P.שינוי_שכר_23_24, P.שינוי_חציון_23_24
    for lab, v in (('mean', y), ('median', ym)):
        r, pv = stats.pearsonr(x, v)
        print('  Δemployment vs Δ%s wage: r=%+.3f (p=%.5f)' % (lab, r, pv))
    sl, ic, r, pv, _ = stats.linregress(x, y)
    print('  slope %.2f%% wage per 1%% employment lost (R2=%.2f)' % (-sl, r ** 2))
    # rank stability, and whether the cluster converges internally
    w16 = c[('wage_work_mean', 2016)].dropna()
    rs, ps = stats.spearmanr(w16, c[('wage_work_mean', 2024)][w16.index])
    rc, pc = stats.pearsonr(w16, 100 * (c[('wage_work_mean', 2024)][w16.index] / w16 - 1))
    print('  rank stability 2016->2024 Spearman=%.3f (p=%.4f) | convergence r=%+.3f (p=%.3f, n=%d)'
          % (rs, ps, rc, pc, len(w16)))
    return P


if __name__ == '__main__':
    c, n = wage_level()
    volumes(c, n)
    spread()
    gender()
    low_pay()
    shift_share()
    authority_profile()
    print('wrote %d tables to %s' % (len(os.listdir(OUT)), os.path.abspath(OUT)))
