"""Readers for the qualitative analysis: its outputs, its report and its insights.

analysis/dashboard-insights.md states figures in prose and tables; analysis/output
holds the tables those figures are supposed to come from. These helpers load both
so the tests can put one against the other.
"""

import json
import os
import re

from . import paths

ANALYSIS_DIR = os.path.join(paths.REPO_ROOT, "analysis")
OUTPUT_DIR = os.path.join(ANALYSIS_DIR, "output")
INSIGHTS_MD = os.path.join(ANALYSIS_DIR, "dashboard-insights.md")
REPORT_HTML = os.path.join(ANALYSIS_DIR, "report.html")
REPORT_DATA = os.path.join(OUTPUT_DIR, "report_data.json")
ETL_DIR = os.path.join(ANALYSIS_DIR, "etl")

# Outputs no script in the repository writes. Their numbers may still be right —
# two of them are checked against the source elsewhere in this suite — but they
# cannot be regenerated, so a change in the data would not reach them.
ORPHAN_OUTPUTS = {
    "dist_vs_peers.csv",
    "self_vs_employee.csv",
    "anaf_authority_ratio.csv",
    "report_data.json",
}


def table(name, index_col=0):
    """One analysis output as a DataFrame."""
    import pandas as pd

    return pd.read_csv(os.path.join(OUTPUT_DIR, name), index_col=index_col)


def report_data():
    with open(REPORT_DATA, encoding="utf-8") as handle:
        return json.load(handle)


def insights_text():
    with open(INSIGHTS_MD, encoding="utf-8") as handle:
        return handle.read()


def insight(number):
    """The Markdown of one numbered insight, without the following ones."""
    text = insights_text()
    match = re.search(
        rf"^##\s*תובנה\s*{number}\s*·(?P<body>.*?)(?=^##\s|\Z)", text, re.S | re.M
    )
    if match is None:
        raise AssertionError(f"insight {number} is not in dashboard-insights.md")
    return match.group("body")


def numbers_in(text):
    """Every number a reader would take as a figure, sign and decimals kept."""
    cleaned = text.replace("‎", "").replace(",", "")
    return [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", cleaned)]


def weighted(values, weights):
    total = sum(weights)
    return sum(value * weight for value, weight in zip(values, weights)) / total


MASTER_PICKLE = "/d/work/master.pkl"
REGIONAL_COUNCILS = ["הגליל העליון", "מרום הגליל", "מבואות החרמון", "גולן"]
TOP_KEYS = ["inc_le3x", "inc_le4x", "inc_gt4x"]


def load_master():
    """The ETL's master table, or None when it has not been built.

    It is derived from relevant_tables.rar by parse_btl.py + build_master.py and is
    not committed, so anything needing it degrades to a skip.
    """
    import os

    if not os.path.exists(MASTER_PICKLE):
        return None
    import pandas as pd

    return pd.read_pickle(MASTER_PICKLE)


def income_shares(master, measure):
    """Cluster authorities' income shares on ONE measure, plus the national row.

    `measure` is 'לחודש עבודה' or 'לחודש בשנה'. The two income-group tables measure
    the same people against different denominators, so mixing them — which
    authority_profile.csv does — puts the two sides of a comparison on different
    scales.
    """
    keys = ["inc_minwage"] + TOP_KEYS
    common = (
        (master.year == 2024)
        & (master.gender == 'סה"כ')
        & (master.population == "כלל העובדים")
        & (master.concept == "כל מקורות ההכנסה")
        & master.mkey.isin(keys)
        & master.src.str.contains(measure)
    )
    local = master[common & (master.cluster == "גליל מזרחי")]
    local = local[
        ((local.level == "יישוב") & (~local.entity.isin(REGIONAL_COUNCILS)))
        | ((local.level == "מועצה אזורית") & (local.entity.isin(REGIONAL_COUNCILS)))
    ]
    table = local.pivot_table(index="entity", columns="mkey", values="value", aggfunc="mean")
    table["top"] = table[TOP_KEYS].sum(axis=1)

    country = master[
        common & (master.level == "נפה/מחוז") & (master.geo1 == 'סה"כ- נפה ומחוז')
    ].pivot_table(columns="mkey", values="value", aggfunc="mean").iloc[0]
    return table, {"minimum": country["inc_minwage"], "top": country[TOP_KEYS].sum()}
