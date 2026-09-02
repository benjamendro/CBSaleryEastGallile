# -*- coding: utf-8 -*-
"""CBS industry x authority table for the cluster (2024).

Small cells are suppressed at source, so each authority carries only the
industries large enough to publish.  Coverage runs from 26% of the authority's
salaried employees to 95%, and the omitted cells are not a random sample —
see missing_cell_wage() — so every figure here is reported with its coverage.
"""
import os
import pandas as pd, numpy as np

ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..')

def load():
    d=pd.read_excel(os.path.join(ROOT,'ענף כלכלי ורשות 1גליל מזרחי.xlsx'),header=2)
    d.columns=['anaf','n','months','wage','rashut']
    d=d[d.anaf.notna()].copy()
    for c in ('n','months','wage'): d[c]=pd.to_numeric(d[c],errors='coerce')
    d['anaf']=d.anaf.astype(str).str.replace(r'\.0$','',regex=True).str.strip()
    d['ענף']=d.anaf.map(names())
    return d

def names():
    dic=pd.read_excel(os.path.join(ROOT,'dicAnaf4SfarotMaster 2.xlsx'),'רשימת הערכים במילון ענפי כלכלה')
    lut=dict(zip(dic.SemelAnaf2Sfarot.dropna().astype(str).str.replace(r'\.0$','',regex=True).str.zfill(2),
                 dic.ShemAnaf2Sfarot))
    out={}
    for code in set(pd.read_excel(os.path.join(ROOT,'ענף כלכלי ורשות 1גליל מזרחי.xlsx'),header=2)
                    .iloc[:,0].dropna().astype(str).str.replace(r'\.0$','',regex=True)):
        parts=[p.strip().zfill(2) for p in code.split('+')]
        nm=[lut[p] for p in parts if p in lut]
        out[code]=(nm[0]+(' +' if len(parts)>1 else '')) if nm else code
    return out

def authority_totals():
    """The published CBS 2024 authority totals, for coverage and validation."""
    c=pd.read_excel(os.path.join(ROOT,'עיבוד לפי ענף ורשות בני דורמבט.xlsx'),
                    'לפי רשויות בנפת צפת וגולן',header=None).iloc[2:,1:6]
    c.columns=['nafa','rashut','n','months','wage']
    c=c[c.rashut.notna()].copy()
    for x in ('n','months','wage'): c[x]=pd.to_numeric(c[x],errors='coerce')
    return c.set_index('rashut')

def national_industry():
    """National and cluster wage per industry, 2024, from the first CBS processing."""
    b=pd.read_excel(os.path.join(ROOT,'עיבוד לפי ענף ורשות בני דורמבט.xlsx'),
                    'לפי ענף כלכלי',header=None).iloc[3:,1:8]
    b.columns=['anaf','n_nat','months_nat','wage_nat','n_eg','months_eg','wage_eg']
    for c in b.columns[1:]: b[c]=pd.to_numeric(b[c],errors='coerce')
    b=b[b.anaf.notna()].copy()
    b['anaf']=b.anaf.astype(str).str.replace(r'\.0$','',regex=True).str.strip()
    return b.set_index('anaf')

def missing_cell_wage():
    """What the suppressed cells must pay for the published total to hold.

    average over the covered cells x covered + X x missing = published total
    """
    d, tot = load(), authority_totals()
    g = d.groupby('rashut')
    r = pd.DataFrame({'covered_n': g.n.sum(),
                      'w_cov': g.apply(lambda x:(x.wage*x.n).sum()/x.n.sum(), include_groups=False)}).join(tot)
    r['missing_n'] = r.n - r.covered_n
    r['coverage'] = 100*r.covered_n/r.n
    r['w_missing'] = (r.n*r.wage - r.covered_n*r.w_cov)/r.missing_n
    r['ratio'] = 100*r.w_missing/r.w_cov
    return r
