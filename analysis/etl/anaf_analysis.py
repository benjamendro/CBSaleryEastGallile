# -*- coding: utf-8 -*-
"""Industry x authority analysis of the second CBS processing (2024).

Coverage caveat that governs everything here: small cells are suppressed at
source, so an authority carries only its larger industries — 26% to 95% of its
salaried employees.  In all 18 authorities the suppressed cells must pay MORE
than the published ones for the authority total to hold (median 123%), so this
file systematically under-represents the top of each local economy.  Figures
are reported only for authorities whose coverage supports them.
"""
import os, sys
import pandas as pd, numpy as np
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anaf_lib import load, national_industry, authority_totals, missing_cell_wage

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
KNOWLEDGE = ['26', '62+63', '72', '64+65+66']     # electronics, ICT, R&D, finance
# the industry file uses the CBS register spelling; the BTL tables use the cluster's
NAMES = {'הגליל העליון': 'גליל עליון', 'מבואות החרמון': 'מבואות חרמון',
         'קריית שמונה': 'קרית שמונה', 'טובא-זנגרייה': 'טובא-זנגריה',
         "ג'ש (גוש חלב)": "גוש חלב(ג'ש)", 'בוקעאתא': 'בוקעתא',
         'עין קנייא': 'עין קיניה', "ע'ג'ר": "עג'ר"}


def save(df, name):
    df.to_csv(os.path.join(OUT, name), encoding='utf-8-sig')
    return df


def coverage():
    r = missing_cell_wage()[['coverage', 'covered_n', 'missing_n', 'w_cov', 'w_missing', 'ratio', 'wage']]
    r.columns = ['כיסוי%', 'שכירים_מכוסים', 'שכירים_חסרים', 'שכר_מכוסה', 'שכר_חסר_משתמע',
                 'יחס_חסר_למכוסה%', 'שכר_מפורסם']
    save(r.sort_values('כיסוי%', ascending=False).round(1), 'anaf_coverage.csv')
    print('  coverage %.0f%%-%.0f%% | suppressed cells pay more in %d/%d authorities (median %.0f%%)'
          % (r['כיסוי%'].min(), r['כיסוי%'].max(),
             (r['יחס_חסר_למכוסה%'] > 100).sum(), len(r), r['יחס_חסר_למכוסה%'].median()))
    return r


def knowledge_share():
    """Knowledge-industry employment share per authority, against its wage index."""
    d, tot = load(), authority_totals()
    k = d[d.anaf.isin(KNOWLEDGE)].groupby('rashut').n.sum()
    cov = 100 * d.groupby('rashut').n.sum() / tot.n
    r = pd.DataFrame({'ידע_שכירים': k, 'כיסוי%': cov}).join(tot[['n', 'wage']]).dropna(subset=['ידע_שכירים'])
    r['ידע%'] = 100 * r['ידע_שכירים'] / r.n
    r['מדד_שכר'] = 100 * r.wage / 12975.83          # CBS national salaried average, 2024
    r.index = [NAMES.get(i, i) for i in r.index]
    rho, p = stats.pearsonr(r['ידע%'], r['מדד_שכר'])
    print('  knowledge share vs wage index: r=%+.3f (p=%.4f, n=%d)' % (rho, p, len(r)))
    save(r.sort_values('ידע%', ascending=False).round(1), 'anaf_knowledge_share.csv')
    return r, rho, p


def education():
    """Education is the only industry published for all 18 authorities."""
    d, nat, tot = load(), national_industry(), authority_totals()
    e = d[d.anaf == '85'].set_index('rashut')[['n', 'months', 'wage']].copy()
    e['יחס_לארצי%'] = 100 * e.wage / nat.loc['85', 'wage_nat']
    e['חלק_מהשכירים%'] = 100 * e.n / tot.n
    e.index = [NAMES.get(i, i) for i in e.index]
    save(e.sort_values('wage', ascending=False).round(1), 'anaf_education.csv')
    print('  education: national %.0f | cluster range %.0f-%.0f | median ratio %.0f%%'
          % (nat.loc['85', 'wage_nat'], e.wage.min(), e.wage.max(), e['יחס_לארצי%'].median()))
    return e


def shift_share_by_authority(min_cov=80):
    """Mix vs within-industry pay, per authority, against a national benchmark
    renormalised to the industries that authority actually publishes."""
    d, nat, tot = load(), national_industry(), authority_totals()
    d['w_nat'] = d.anaf.map(nat.wage_nat)
    rows = []
    for a, g in d.groupby('rashut'):
        cov = 100 * g.n.sum() / tot.loc[a, 'n']
        g = g.dropna(subset=['w_nat'])
        if cov < min_cov or len(g) < 5:
            continue
        s_a = (g.n / g.n.sum()).values
        s_n = nat.loc[g.anaf, 'n_nat'].values
        s_n = s_n / s_n.sum()
        Wa, Wn = (s_a * g.wage.values).sum(), (s_n * g.w_nat.values).sum()
        rows.append(dict(רשות=NAMES.get(a, a), כיסוי=cov, שכר=Wa, ארצי_מתוקנן=Wn, פער=Wa - Wn,
                         הרכב=((s_a - s_n) * ((g.wage.values + g.w_nat.values) / 2)).sum(),
                         שכר_בתוך_ענף=(((s_a + s_n) / 2) * (g.wage.values - g.w_nat.values)).sum()))
    S = pd.DataFrame(rows).set_index('רשות').sort_values('פער')
    S['שארית'] = S.פער - S.הרכב - S.שכר_בתוך_ענף
    save(S.round(1), 'anaf_shiftshare_authority.csv')
    print('  per-authority shift-share on %d authorities (coverage >= %d%%), max residual %.6f'
          % (len(S), min_cov, S.שארית.abs().max()))
    return S


def same_industry_spread(min_auth=10):
    """How far the same industry's pay travels between authorities."""
    d, nat = load(), national_industry()
    d['יחס'] = 100 * d.wage / d.anaf.map(nat.wage_nat)
    g = d.groupby(['anaf', 'ענף']).agg(רשויות=('rashut', 'nunique'), שכירים=('n', 'sum'),
                                       מינימום=('wage', 'min'), מקסימום=('wage', 'max'),
                                       יחס_חציוני=('יחס', 'median'))
    g = g[g.רשויות >= min_auth].copy()
    g['פי'] = g.מקסימום / g.מינימום
    save(g.sort_values('פי', ascending=False).round(1), 'anaf_industry_spread.csv')
    return g


def growth_link():
    """Does the 2024 knowledge share track earlier wage growth?  n=9 — reported
    with its p-value precisely because it does not reach significance."""
    from lib import M, RC
    r, _, _ = knowledge_share()
    b = M[(M.cluster == 'גליל מזרחי') & (M.mkey == 'wage_work_mean') &
          (M.population == 'כלל העובדים') & (M.concept == 'כל מקורות ההכנסה') &
          (M.gender == 'סה"כ') & M.year.isin([2016, 2022, 2024])]
    b = b[((b.level == 'יישוב') & (~b.entity.isin(RC))) |
          ((b.level == 'מועצה אזורית') & (b.entity.isin(RC)))]
    bp = b.pivot_table(index='eshkol_name', columns='year', values='value', aggfunc='mean')
    bp['צמיחה_16_22'] = 100 * (bp[2022] / bp[2016] - 1)
    bp['צמיחה_22_24'] = 100 * (bp[2024] / bp[2022] - 1)
    J = r[['ידע%', 'מדד_שכר']].join(bp[['צמיחה_16_22', 'צמיחה_22_24']]).dropna()
    out = {}
    for col in ('צמיחה_16_22', 'צמיחה_22_24'):
        rho, p = stats.pearsonr(J['ידע%'], J[col])
        out[col] = (rho, p)
        print('  knowledge share vs %s: r=%+.3f (p=%.3f, n=%d)' % (col, rho, p, len(J)))
    save(J.round(1), 'anaf_growth_link.csv')
    return J, out


if __name__ == '__main__':
    coverage(); knowledge_share(); education()
    shift_share_by_authority(); same_industry_spread(); growth_link()
    print('done')
