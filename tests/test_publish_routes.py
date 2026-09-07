"""Two publish routes, one dashboard.

CLAUDE.md, "שני ניתובי הפרסום": build.py always writes two pairs of pages from
one set of data. The internal pair (index.html / artifact.html) carries the
hand-written insights; the public pair (index_public.html / artifact_public.html)
is the same data and the same charts with no link to the insights and no access
to them — an insight is interpretation, and it has to pass an expert before it
is published.

The promise has two halves and both are machine-checkable: the public pages must
carry no insight content, and they must carry everything else unchanged. The
first half is what the GitHub Pages workflow serves to the world, so it is
checked here on the committed files and again on a build made to leak.
"""

import json
import os

import pytest

from _lib import paths, project

# a string no real insight would contain, injected to watch where it comes out
SENTINEL = "SENTINEL-INSIGHT-שאסור-לה-להגיע-לניתוב-הציבורי"


# --- which route each published page declares ---------------------------------

def test_should_declare_the_internal_route_on_the_pages_that_carry_insights(
    index_html, artifact_html
):
    # Arrange / Act / Assert
    for name, page in (("index.html", index_html), ("artifact.html", artifact_html)):
        assert project.INTERNAL_ROUTE in page, (
            f"dashboard/{name} does not declare the internal route — rebuild it"
        )
        assert project.PUBLIC_ROUTE not in page, (
            f"dashboard/{name} declares the public route; it is the internal page"
        )


def test_should_declare_the_public_route_on_the_pages_published_outward(
    index_public_html, artifact_public_html
):
    # Arrange / Act / Assert
    for name, page in (
        ("index_public.html", index_public_html),
        ("artifact_public.html", artifact_public_html),
    ):
        assert project.PUBLIC_ROUTE in page, (
            f"dashboard/{name} does not declare the public route — the insights "
            "would stay reachable on the page published outward"
        )
        assert project.INTERNAL_ROUTE not in page, (
            f"dashboard/{name} declares the internal route; it is the public page"
        )


# --- the public route carries no interpretation -------------------------------

def test_should_carry_no_insight_content_in_the_public_page(index_public_html):
    # Arrange
    payload = project.embedded_payload(index_public_html)

    # Act / Assert
    assert payload["insights"] == [], (
        "dashboard/index_public.html embeds insight content — it must be emptied "
        "before injection, not merely hidden in the page"
    )


@pytest.mark.slow
def test_should_never_write_an_insight_into_the_public_pages(tmp_path, data, btl):
    """Build both routes from data that does carry an insight, and follow it."""
    # Arrange
    sandbox = project.make_sandbox(str(tmp_path / "routes"))
    leaking = dict(data, insights=[{"section": "auth", "title": SENTINEL, "body": SENTINEL}])
    for name, payload in (("data.json", leaking), ("btl.json", btl)):
        with open(os.path.join(sandbox, "dashboard", name), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)

    # Act
    result = project.run_build("build.py", sandbox)

    # Assert
    assert result.returncode == 0, f"build.py failed:\n{result.stderr[-2000:]}"
    for name in ("index.html", "artifact.html"):
        page = project.read_text(os.path.join(sandbox, "dashboard", name))
        assert SENTINEL in page, f"the internal {name} lost the insight it is meant to carry"
    for name in ("index_public.html", "artifact_public.html"):
        page = project.read_text(os.path.join(sandbox, "dashboard", name))
        assert SENTINEL not in page, (
            f"an insight reached dashboard/{name} — the public route leaks the "
            "interpretation it exists to withhold"
        )


# --- and everything else is identical -----------------------------------------

def test_should_show_the_same_data_on_both_routes(index_html, index_public_html):
    """Same numbers, same charts — the routes differ in the insights and nothing else."""
    # Arrange
    internal = project.embedded_payload(index_html)
    public = project.embedded_payload(index_public_html)

    # Act
    without_insights = (
        {key: value for key, value in internal.items() if key != "insights"},
        {key: value for key, value in public.items() if key != "insights"},
    )

    # Assert
    assert without_insights[0] == without_insights[1], (
        "the public route no longer shows the same data as the internal one"
    )


def test_should_keep_the_route_flag_out_of_the_embedded_data(index_html, index_public_html):
    """The flag rides its own marker, so the payload stays exactly data.json + btl.json."""
    # Arrange / Act / Assert
    for name, page in (
        ("index.html", index_html),
        ("index_public.html", index_public_html),
    ):
        assert "public" not in project.embedded_payload(page), (
            f"dashboard/{name} carries the route flag inside DATA — it belongs in "
            "the __PUBLIC__ marker, so the embedded payload stays traceable to data.json"
        )


def test_should_publish_the_public_artifact_inside_the_standalone_wrapper(
    index_public_html, artifact_public_html
):
    # Arrange / Act / Assert
    assert artifact_public_html.strip() in index_public_html, (
        "index_public.html is not artifact_public.html wrapped — the two have diverged"
    )


def test_should_leave_no_unfilled_injection_marker_in_the_public_page(index_public_html):
    # Arrange / Act / Assert
    for marker in (project.DATA_MARKER, project.LOGO_MARKER, project.PUBLIC_MARKER):
        assert marker not in index_public_html, f"the {marker} marker was never replaced"


def test_should_still_carry_the_edit_controls_on_the_internal_route(index_html):
    """Editing is an internal working tool; the internal page keeps it."""
    # Arrange / Act / Assert
    for control in ('id="editToggle"', 'id="editbar"'):
        assert control in index_html, (
            f"dashboard/index.html lost {control} — editing is the internal route's tool"
        )


def test_should_keep_the_public_route_reachable_from_the_build(index_public_html):
    """The six data sections and their "על הנתונים" drawers survive the stripping."""
    # Arrange
    sections = ("auth", "change", "anaf", "mix", "dist", "trend")

    # Act / Assert
    for section in sections:
        assert f'id="b-{section}"' in index_public_html, (
            f'the public page lost the "על הנתונים" drawer of section {section}'
        )
        assert f'id="sec-{section}"' in index_public_html, (
            f"the public page lost section {section} itself"
        )


def test_should_publish_four_pages_from_one_build():
    # Arrange / Act / Assert
    for name in paths.PUBLISHED_PAGES:
        path = os.path.join(paths.DASHBOARD_DIR, name)
        assert os.path.exists(path), (
            f"dashboard/{name} is missing — build.py writes both routes in one run"
        )
