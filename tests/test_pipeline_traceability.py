"""Does every figure on the dashboard come from the raw data?

The chain the dashboard rests on has two links, and this module checks both by
re-running them rather than by trusting them:

    source workbooks --build_data.py-->  data.json  --.
    National Insurance --build_btl.py--> btl.json  --+--build.py--> index.html
                                          template.html --'

Each build is re-run inside a sandbox copy, and its output compared byte for
byte with what the repository publishes. A hand-edit anywhere along the chain —
which dashboard/README.md and CLAUDE.md both forbid — makes one of these fail.
"""

import filecmp
import os
import shutil

import pytest

from _lib import paths, project

pytestmark = pytest.mark.traceability

YEAR_RE = r"(?<!\d)(19|20)\d{2}(?!\d)"


# --- link 1: raw workbooks -> processed data ----------------------------------

@pytest.mark.slow
def test_should_rebuild_data_json_from_the_source_workbooks(sandbox):
    """data.json must be exactly what build_data.py derives from the CBS files."""
    # Arrange
    rebuilt = os.path.join(sandbox, "dashboard", "data.json")
    os.remove(rebuilt)

    # Act
    result = project.run_build("build_data.py", sandbox)

    # Assert
    assert result.returncode == 0, f"build_data.py failed:\n{result.stderr[-2000:]}"
    assert os.path.exists(rebuilt), "build_data.py did not write data.json"
    assert filecmp.cmp(paths.DATA_JSON, rebuilt, shallow=False), (
        "dashboard/data.json differs from what build_data.py produces — it was "
        "hand-edited, or the pipeline changed without the data being rebuilt"
    )


@pytest.mark.slow
def test_should_rebuild_btl_json_from_the_national_insurance_tables(sandbox, btl_tables):
    """btl.json must be exactly what build_btl.py derives from the 175 BTL tables."""
    # Arrange
    rebuilt = os.path.join(sandbox, "dashboard", "btl.json")
    os.remove(rebuilt)

    # Act
    result = project.run_build("build_btl.py", sandbox, {"BTL_DIR": btl_tables})

    # Assert
    assert result.returncode == 0, f"build_btl.py failed:\n{result.stderr[-2000:]}"
    assert os.path.exists(rebuilt), "build_btl.py did not write btl.json"
    assert filecmp.cmp(paths.BTL_JSON, rebuilt, shallow=False), (
        "dashboard/btl.json differs from what build_btl.py produces"
    )


# --- link 2: processed data -> published page ---------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("page", ["index.html", "artifact.html"])
def test_should_rebuild_the_published_page_from_the_template_and_the_data(sandbox, page):
    """The page must be exactly template.html + data.json + btl.json + the logo."""
    # Arrange
    rebuilt = os.path.join(sandbox, "dashboard", page)
    published = os.path.join(paths.DASHBOARD_DIR, page)
    # restore the committed data files in case an earlier test removed them
    for name in ("data.json", "btl.json"):
        shutil.copy2(
            os.path.join(paths.DASHBOARD_DIR, name),
            os.path.join(sandbox, "dashboard", name),
        )
    if os.path.exists(rebuilt):
        os.remove(rebuilt)

    # Act
    result = project.run_build("build.py", sandbox)

    # Assert
    assert result.returncode == 0, f"build.py failed:\n{result.stderr[-2000:]}"
    assert filecmp.cmp(published, rebuilt, shallow=False), (
        f"dashboard/{page} is not what build.py produces from template.html and the "
        "data files — CLAUDE.md forbids editing it by hand"
    )


# --- the payload the page actually carries ------------------------------------

def test_should_carry_the_committed_part_a_data_in_the_published_page(published_payload, data):
    # Arrange
    carried = {key: value for key, value in published_payload.items() if key != "btl2"}

    # Act / Assert
    assert carried == data, (
        "the data embedded in index.html is not dashboard/data.json"
    )


def test_should_carry_the_committed_part_b_data_in_the_published_page(published_payload, btl):
    # Arrange / Act / Assert
    assert published_payload["btl2"] == btl, (
        "the part-B data embedded in index.html is not dashboard/btl.json"
    )


def test_should_embed_the_same_payload_in_both_published_pages(index_html, artifact_html):
    # Arrange / Act
    from_index = project.embedded_payload(index_html)
    from_artifact = project.embedded_payload(artifact_html)

    # Assert
    assert from_index == from_artifact, (
        "index.html and artifact.html disagree on the data they display"
    )


def test_should_publish_the_artifact_as_the_page_inside_the_standalone_wrapper(
    index_html, artifact_html
):
    """index.html is artifact.html plus an <html>/<head>/<body> wrapper, nothing else."""
    # Arrange / Act / Assert
    assert artifact_html.strip() in index_html, (
        "index.html is not artifact.html wrapped — the two outputs have diverged"
    )


def test_should_leave_no_unfilled_injection_marker_in_the_published_page(index_html):
    # Arrange / Act / Assert
    assert project.DATA_MARKER not in index_html, "the data marker was never replaced"
    assert project.LOGO_MARKER not in index_html, "the logo marker was never replaced"


# --- no figure may be written into the page by hand ---------------------------

def test_should_keep_every_figure_out_of_the_template_markup(template_html):
    """The template's markup must carry no data — only structure and labels.

    Styles, chart code and the web-font link legitimately contain numbers
    (geometry, weights). Everything else that survives is a literal a reader
    would take as a finding, and findings must come from DATA.
    """
    # Arrange
    import re

    markup = project.template_without_code_constants(template_html)
    markup = re.sub(r"<link\b[^>]*>", " ", markup, flags=re.I)

    # Act
    literals = [
        match.group()
        for match in project.NUMBER_RE.finditer(markup)
        if not re.fullmatch(YEAR_RE, match.group())
    ]

    # Assert
    assert literals == [], (
        f"figures hardcoded into the template instead of read from DATA: {literals}"
    )


def test_should_only_name_years_the_data_actually_covers(template_html, data, btl):
    """A year printed in the markup must be a year the data speaks for."""
    # Arrange
    import re

    markup = project.template_without_code_constants(template_html)
    markup = re.sub(r"<link\b[^>]*>", " ", markup, flags=re.I)
    covered = {str(data["meta"]["year"]), str(data["change"]["year"])}
    covered |= {str(year) for year in btl["meta"]["years"]}
    covered |= {str(row["year"]) for row in data["btl"]["rows"]}

    # Act
    named = {match.group() for match in re.finditer(YEAR_RE, markup)}

    # Assert
    assert named <= covered, (
        f"the page names years the data does not cover: {sorted(named - covered)} "
        f"(covered: {sorted(covered)})"
    )
