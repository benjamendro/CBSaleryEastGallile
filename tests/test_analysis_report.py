"""The wage report, and the reproducibility of what feeds it.

analysis/report.html is generated from analysis/output/report_data.json by
build_report.py. These tests re-run that build, cross-check the data file against
the outputs the ETL does regenerate, and record where the chain breaks.
"""

import filecmp
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import pytest

from _lib import analysis, paths

pytestmark = pytest.mark.traceability

TOL = 0.06


@pytest.fixture(scope="module")
def data():
    return analysis.report_data()


# --- the report is built from the data file -----------------------------------

@pytest.mark.slow
def test_should_rebuild_the_report_from_its_data_file(tmp_path_factory):
    """report.html must be exactly what build_report.py makes of report_data.json."""
    # Arrange
    sandbox = str(tmp_path_factory.mktemp("report"))
    for folder in ("etl", "src", "output"):
        shutil.copytree(
            os.path.join(analysis.ANALYSIS_DIR, folder),
            os.path.join(sandbox, folder),
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    shutil.copy2(analysis.REPORT_HTML, os.path.join(sandbox, "report.html"))

    # Act
    result = subprocess.run(
        [sys.executable, os.path.join(sandbox, "etl", "build_report.py")],
        capture_output=True, text=True, timeout=600,
    )

    # Assert
    assert result.returncode == 0, f"build_report.py failed:\n{result.stderr[-1500:]}"
    assert filecmp.cmp(
        analysis.REPORT_HTML, os.path.join(sandbox, "report.html"), shallow=False
    ), "analysis/report.html is not what build_report.py produces — it was hand-edited"


def test_should_name_the_cluster_in_the_reports_title():
    # Arrange / Act
    with open(analysis.REPORT_HTML, encoding="utf-8") as handle:
        html = handle.read()

    # Assert
    assert "<title>שכר באשכול גליל מזרחי</title>" in html


# --- the data file agrees with the outputs the ETL does regenerate ------------

def test_should_carry_the_same_wage_series_as_the_regenerated_tables(data):
    # Arrange
    mismatches = []

    # Act
    for key, name in (
        ("idx_year", "idx_wage_year_mean.csv"),
        ("idx_work", "idx_wage_work_mean.csv"),
        ("wage_abs", "wage_wage_year_mean.csv"),
    ):
        table = analysis.table(name)
        for column, series in data[key].items():
            if column not in table.columns:
                mismatches.append((key, column, "column missing from the table"))
                continue
            drift = np.nanmax(np.abs(np.asarray(series, dtype=float) - table[column].values))
            if drift > TOL:
                mismatches.append((key, column, round(float(drift), 3)))

    # Assert
    assert mismatches == [], f"the report's series diverge from the outputs: {mismatches}"


def test_should_carry_the_same_authority_figures_as_the_profile_table(data):
    # Arrange
    import pandas as pd

    profile = analysis.table("authority_profile.csv")
    authorities = pd.DataFrame(data["auth"]).set_index("name")
    columns = {
        "n": "מועסקים", "mean": "שכר_ממוצע", "med": "שכר_חציוני",
        "idx": "מדד_ממוצע", "idxm": "מדד_חציון", "rank": "מקום_ארצי",
    }

    # Act
    mismatches = []
    for key, column in columns.items():
        drift = np.nanmax(
            np.abs(authorities[key].reindex(profile.index).astype(float).values
                   - profile[column].astype(float).values)
        )
        if drift > TOL:
            mismatches.append((key, column, round(float(drift), 3)))

    # Assert
    assert set(authorities.index) == set(profile.index), "the report covers other authorities"
    assert mismatches == [], f"the report's authority figures diverge: {mismatches}"


def test_should_carry_the_same_income_distribution_as_the_outputs(data):
    # Arrange
    table = analysis.table("income_dist.csv")

    # Act
    mismatches = [
        (column, round(float(np.nanmax(np.abs(np.asarray(values, dtype=float)
                                              - table[column].values))), 3))
        for column, values in data["inc"].items()
        if column in table.columns
        and np.nanmax(np.abs(np.asarray(values, dtype=float) - table[column].values)) > TOL
    ]

    # Assert
    assert mismatches == [], f"the report's income distribution diverges: {mismatches}"


# --- where the chain breaks ---------------------------------------------------

ETL_SCRIPTS = ("analyze.py", "anaf_analysis.py", "anaf22_analysis.py", "build_report.py")
MASTER = "/d/work/master.pkl"


@pytest.fixture(scope="module")
def refreshed_outputs(tmp_path_factory):
    """Which output files a full ETL re-run actually rewrites.

    Asked empirically rather than by reading the scripts: names are built inside
    loops, so scanning for write targets misses real generators and invents
    others. The ETL reads a master pickle that is not in the repository, so this
    skips wherever that has not been built.
    """
    if not os.path.exists(MASTER):
        pytest.skip(
            f"{MASTER} is absent — build it with analysis/etl/parse_btl.py and "
            "build_master.py to run the reproducibility checks"
        )
    root = str(tmp_path_factory.mktemp("etlroot"))
    sandbox = os.path.join(root, "analysis")
    for folder in ("etl", "src", "output"):
        shutil.copytree(
            os.path.join(analysis.ANALYSIS_DIR, folder),
            os.path.join(sandbox, folder),
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    # the industry scripts read the CBS workbooks from the repository root
    for name in os.listdir(paths.REPO_ROOT):
        if name.endswith(".xlsx"):
            shutil.copy2(os.path.join(paths.REPO_ROOT, name), os.path.join(root, name))
    output = os.path.join(sandbox, "output")
    for name in os.listdir(output):
        os.utime(os.path.join(output, name), (0, 0))
    for script in ETL_SCRIPTS:
        subprocess.run(
            [sys.executable, os.path.join(sandbox, "etl", script)],
            capture_output=True, text=True, timeout=1800,
        )
    return {
        name for name in os.listdir(output)
        if name.endswith((".csv", ".json"))
        and os.path.getmtime(os.path.join(output, name)) > 0
    }


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN GAP: four files in analysis/output have no generator in the repository — "
        "dist_vs_peers.csv (the whole evidence base of insight 2), self_vs_employee.csv "
        "(insight 9), anaf_authority_ratio.csv (insight 11) and report_data.json (every "
        "figure in the report). Their numbers check out — dist_vs_peers.csv was "
        "reproduced by hand from the master and matched to the last decimal, and "
        "report_data.json agrees with the tables the ETL does write — but a change in "
        "the data would never reach them. Delete this marker once the scripts that "
        "build them are committed."
    ),
)
def test_should_generate_every_analysis_output_from_a_committed_script(refreshed_outputs):
    # Arrange
    published = {f for f in os.listdir(analysis.OUTPUT_DIR) if f.endswith((".csv", ".json"))}

    # Act
    orphans = published - refreshed_outputs

    # Assert
    assert orphans == set(), f"outputs no script rewrites: {sorted(orphans)}"


@pytest.mark.slow
def test_should_pin_which_analysis_outputs_are_orphaned(refreshed_outputs):
    """Pins the gap above so it cannot widen unnoticed."""
    # Arrange
    published = {f for f in os.listdir(analysis.OUTPUT_DIR) if f.endswith((".csv", ".json"))}

    # Act
    orphans = published - refreshed_outputs

    # Assert
    assert orphans == analysis.ORPHAN_OUTPUTS, (
        f"the set of ungenerated outputs changed: {sorted(orphans)}"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN DEFECT: analysis/output is stale relative to analysis/etl. The ETL now "
        "labels the income bands 'עד שכר המינימום' / 'מינימום – 75% מהממוצע', which is "
        "what report_data.json already carries, but income_dist.csv still holds the "
        "older 'עד שכר מינימום' / 'עד 75% מהממוצע'. The values agree; only the tables "
        "were not rewritten after the rename."
    ),
)
def test_should_label_the_income_bands_the_same_way_everywhere(data):
    # Arrange
    table = analysis.table("income_dist.csv")

    # Act / Assert
    assert list(table.index) == data["inc_rows"], (
        f"income_dist.csv rows {list(table.index)} vs the report's {data['inc_rows']}"
    )


def test_should_pin_the_stale_income_band_labels(data):
    """Pins the rename above: same values, different labels."""
    # Arrange
    table = analysis.table("income_dist.csv")

    # Act / Assert
    assert len(table.index) == len(data["inc_rows"]) == 7
    assert list(table.index) != data["inc_rows"], (
        "the labels now agree — remove the xfail above and this pin with it"
    )
    for column, values in data["inc"].items():
        if column in table.columns:
            assert np.allclose(np.asarray(values, dtype=float), table[column].values, atol=TOL), (
                f"the {column} values diverged as well, which the rename does not explain"
            )
