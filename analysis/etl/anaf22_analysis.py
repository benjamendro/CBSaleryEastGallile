# -*- coding: utf-8 -*-
"""2022 industry x authority x district analysis, and the 2022->2024 comparison.

The 2022 and 2024 CBS processings share a producer and a definition (annual salary
divided by months worked, salary income only), so they are directly comparable —
unlike either against the BTL tables.  Two things the 2022 file adds that 2024
cannot: a full district breakdown, which gives a national benchmark and a
'northern district excluding the cluster' comparator; and far better cell
coverage (median 94% of an authority's employees against 80%), which is what
makes all 18 authorities analysable rather than 9.
"""
import os, sys
import pandas as pd, numpy as np
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anaf22_lib as L22
from anaf_lib import load as load24, national_industry, authority_totals as tot24

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
KNOWLEDGE = ['26', '62+63', '72', '64+65+66']
NAT22, NAT24 = 11986.0, 12975.83


def save(df, name):
    df.to_csv(os.path.join(OUT, name), encoding='utf-8-sig')
    return df


def _wm(n, w):
    return (n * w).sum() / n.sum()


def matched():
    """Cluster and national, by industry, on the 2024 grouping, both years."""
    n24 = national_industry()
    groups = list(n24.index.astype(str))
    d = L22.districts()
    cl = L22.harmonise(d[d.mahoz == L22.CLUSTER], groups).set_index('grp')
    na = L22.harmonise(d.assign(mahoz='ALL'), groups).set_index('grp')
    C = pd.DataFrame({'n22': cl.n, 'w22': cl.wage, 'N22': na.n, 'W22': na.wage,
                      'n24': n24.n_eg, 'w24': n24.wage_eg,
                      'N24': n24.n_nat, 'W24': n24.wage_nat}).dropna()
    C['dn'] = 100 * (C.n24 / C.n22 - 1)
    C['dn_nat'] = 100 * (C.N24 / C.N22 - 1)
    C['dw'] = 100 * (C.w24 / C.w22 - 1)
    C['ratio22'] = 100 * C.w22 / C.W22
    C['ratio24'] = 100 * C.w24 / C.W24
    C['dratio'] = C.ratio24 - C.ratio22
    save(C.round(1), 'anaf22_industry_change.csv')
    print('  cluster %.0f -> %.0f (index %.1f -> %.1f) | employment %+.1f%% vs national %+.1f%%'
          % (_wm(C.n22, C.w22), _wm(C.n24, C.w24),
             100 * _wm(C.n22, C.w22) / _wm(C.N22, C.W22),
             100 * _wm(C.n24, C.w24) / _wm(C.N24, C.W24),
             100 * (C.n24.sum() / C.n22.sum() - 1), 100 * (C.N24.sum() / C.N22.sum() - 1)))
    b = C[C.n22 >= 500]
    r, p = stats.pearsonr(b.dn, b.dratio)
    print('  industry: employment change vs wage-ratio change r=%+.3f (p=%.4f, n=%d)' % (r, p, len(b)))
    return C


def districts_2022():
    d = L22.districts()
    g = d.groupby('mahoz')
    t = pd.DataFrame({'שכירים': g.n.sum(),
                      'שכר': g.apply(lambda x: _wm(x.n, x.wage), include_groups=False)})
    t['מדד'] = 100 * t.שכר / NAT22
    save(t.sort_values('מדד', ascending=False).round(1), 'anaf22_districts.csv')
    cl, nr = t.loc[L22.CLUSTER, 'שכר'], t.loc[L22.NORTH_REST, 'שכר']
    gap = NAT22 - cl
    print('  2022 geography: cluster %.0f | north-rest %.0f | national %.0f' % (cl, nr, NAT22))
    print('  gap %.0f = north-vs-national %.0f (%.0f%%) + cluster-vs-north %.0f (%.0f%%)'
          % (gap, NAT22 - nr, 100 * (NAT22 - nr) / gap, nr - cl, 100 * (nr - cl) / gap))
    return t


def authorities_2022_2024():
    t22, t24 = L22.authority_totals(), tot24()
    t24.index = [L22.NAMES.get(i, i) for i in t24.index]
    r = pd.DataFrame({'שכירים_22': t22.n, 'שכר_22': t22.wage,
                      'שכירים_24': t24.n, 'שכר_24': t24.wage})
    r['מדד_22'] = 100 * r.שכר_22 / NAT22
    r['מדד_24'] = 100 * r.שכר_24 / NAT24
    r['שינוי_מדד'] = r.מדד_24 - r.מדד_22
    r['שינוי_תעסוקה%'] = 100 * (r.שכירים_24 / r.שכירים_22 - 1)
    r['שינוי_שכר%'] = 100 * (r.שכר_24 / r.שכר_22 - 1)
    a22 = L22.harmonise(L22.authorities(), list(national_industry().index.astype(str)))
    a24 = load24()
    a24['rashut'] = a24.rashut.map(lambda x: L22.NAMES.get(x, x))
    r['ידע%_22'] = 100 * a22[a22.grp.isin(KNOWLEDGE)].groupby('rashut').n.sum() / r.שכירים_22
    r['ידע%_24'] = 100 * a24[a24.anaf.isin(KNOWLEDGE)].groupby('rashut').n.sum() / r.שכירים_24
    r['כיסוי_22'] = 100 * a22.groupby('rashut').n.sum() / r.שכירים_22
    save(r.sort_values('מדד_22', ascending=False).round(1), 'anaf22_authorities.csv')
    k = r.dropna(subset=['שכר_22', 'שכר_24'])
    rs, ps = stats.spearmanr(k.שכר_22, k.שכר_24)
    rr, pp = stats.pearsonr(k['שינוי_תעסוקה%'], k.שינוי_מדד)
    print('  authority rank 2022->2024 Spearman=%.3f (p=%.5f) | Δemployment vs Δindex r=%+.3f (p=%.4f)'
          % (rs, ps, rr, pp))
    print('  spread high/low %.2f -> %.2f | CV %.1f%% -> %.1f%%'
          % (k.שכר_22.max() / k.שכר_22.min(), k.שכר_24.max() / k.שכר_24.min(),
             100 * k.שכר_22.std() / k.שכר_22.mean(), 100 * k.שכר_24.std() / k.שכר_24.mean()))
    return r


if __name__ == '__main__':
    matched(); districts_2022(); authorities_2022_2024()
    print('done')
