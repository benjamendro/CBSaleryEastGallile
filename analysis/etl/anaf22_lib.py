# -*- coding: utf-8 -*-
"""CBS 'שכירים ושכר ממוצע לפי מחוזות ורשויות בצפון', 2022.

Same producer, same definitions as the 2024 processings (annual salary divided by
months worked, salary income only, anyone with salary income during the year), so
the two years are directly comparable.  Two differences matter:
  * 2022 publishes plain 2-digit industry codes (77 of them); 2024 publishes 51
    groups such as '62+63'.  harmonise() folds 2022 into the 2024 groups — every
    2022 code maps except code 9 (126 employees nationally).
  * 2022 coverage at the 2-digit level is far better: 75%-98% of an authority's
    employees, median 94%, against 26%-95% in the 2024 industry-by-authority file.
The sheets also carry Excel pivot leftovers in trailing columns, which are dropped.
"""
import os
import pandas as pd, numpy as np

ROOT = os.environ.get('EG_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
F = os.path.join(ROOT, 'שכירים ושכר ממוצע לפי מחוזות ורשויות בצפון 2022_10.7.24.xlsx')
CLUSTER = 'נפות צפת וגולן'          # == the cluster's 18 authorities
NORTH_REST = 'מחוז צפון ללא'        # northern district minus the cluster
# the CBS register spelling used here vs the cluster's own list
NAMES = {'הגליל העליון': 'גליל עליון', 'מבואות החרמון': 'מבואות חרמון',
         'קריית שמונה': 'קרית שמונה', 'טובא-זנגרייה': 'טובא-זנגריה',
         "ג'ש (גוש חלב)": "גוש חלב(ג'ש)", 'בוקעאתא': 'בוקעתא',
         'עין קנייא': 'עין קיניה', "ע'ג'ר": "עג'ר"}


def _num(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def authorities():
    d = pd.read_excel(F, 'רשויות_ענף_כלכלי__2ספרות_', header=0).iloc[:, :5]
    d.columns = ['rashut', 'anaf', 'anaf_name', 'n', 'wage']
    d = _num(d[d.rashut.notna()].copy(), ['n', 'wage'])
    d['anaf'] = d.anaf.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    d['rashut'] = d.rashut.map(lambda x: NAMES.get(x, x))
    return d


def districts():
    d = pd.read_excel(F, 'מחוז_ענף_כלכלי_2_ספרות', header=0).iloc[:, :4]
    d.columns = ['mahoz', 'anaf', 'n', 'wage']
    d = _num(d[d.mahoz.notna()].copy(), ['n', 'wage'])
    d['anaf'] = d.anaf.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    return d


def authority_totals():
    """Includes the '*' rows — employees with no industry — so this is the true total."""
    s = pd.read_excel(F, 'רשויות_ענף_כלכלי__סדר_', header=0).iloc[:, :4]
    s.columns = ['rashut', 'sec', 'n', 'wage']
    s = _num(s[s.rashut.notna() & s.sec.notna()].copy(), ['n', 'wage'])
    s['rashut'] = s.rashut.map(lambda x: NAMES.get(x, x))
    g = s.groupby('rashut')
    return pd.DataFrame({'n': g.n.sum(),
                         'wage': g.apply(lambda x: (x.wage * x.n).sum() / x.n.sum(), include_groups=False),
                         'no_industry': s[s.sec == '*'].groupby('rashut').n.sum()})


def harmonise(df, groups, key='anaf'):
    """Fold the 2022 2-digit codes into the 2024 groups, re-weighting the wage."""
    mem = {p.strip(): g for g in groups for p in str(g).split('+')}
    d = df.copy()
    d['grp'] = d[key].map(mem)
    d = d[d.grp.notna()]
    idx = [c for c in ('rashut', 'mahoz') if c in d.columns] + ['grp']
    g = d.groupby(idx)
    out = pd.DataFrame({'n': g.n.sum(),
                        'wage': g.apply(lambda x: (x.wage * x.n).sum() / x.n.sum(), include_groups=False)})
    return out.reset_index()


def national():
    """2022 national totals per 2-digit code, aggregated over the eight districts."""
    d = districts()
    g = d.groupby('anaf')
    return pd.DataFrame({'n': g.n.sum(),
                         'wage': g.apply(lambda x: (x.wage * x.n).sum() / x.n.sum(), include_groups=False)})
