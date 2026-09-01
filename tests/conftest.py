"""Shared fixtures for the reliability suite.

Nothing here is mocked. The suite exists to check the real artefacts — the real
workbooks, the real pipeline, the real published page — so the only test double
anywhere is at a genuinely external boundary (Chart-less SVG rendering in the
Vitest suite). Expensive reads are session-scoped and done once.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _lib import eshkol as eshkol_lib  # noqa: E402
from _lib import paths, project  # noqa: E402


@pytest.fixture(scope="session")
def data():
    """dashboard/data.json — part A, CBS 2024."""
    return project.load_data()


@pytest.fixture(scope="session")
def btl():
    """dashboard/btl.json — part B, National Insurance 2016–2024."""
    return project.load_btl()


@pytest.fixture(scope="session")
def index_html():
    """The published standalone dashboard."""
    return project.read_text(paths.INDEX_HTML)


@pytest.fixture(scope="session")
def artifact_html():
    """The same page in its Artifact wrapper-less form."""
    return project.read_text(paths.ARTIFACT_HTML)


@pytest.fixture(scope="session")
def template_html():
    """The page before data injection."""
    return project.read_text(paths.TEMPLATE_HTML)


@pytest.fixture(scope="session")
def published_payload(index_html):
    """The JSON object build.py injected into index.html."""
    return project.embedded_payload(index_html)


@pytest.fixture(scope="session")
def sandbox(tmp_path_factory):
    """An isolated copy of everything the pipeline reads, built once per session."""
    return project.make_sandbox(str(tmp_path_factory.mktemp("pipeline")))


@pytest.fixture(scope="session")
def btl_tables():
    """The extracted National Insurance workbooks, or a skip when unavailable."""
    if not os.path.exists(paths.RELEVANT_TABLES_RAR):
        pytest.skip("relevant_tables.rar is not in the checkout")
    if paths.extraction_tool() is None:
        pytest.skip(
            "no RAR5 extractor on PATH — install libarchive-tools for bsdtar "
            "(p7zip 16.x silently fails on this archive)"
        )
    directory = paths.btl_tables_dir()
    if directory is None:
        pytest.skip("relevant_tables.rar could not be extracted")
    return directory


@pytest.fixture(scope="session")
def matcher_module():
    """The project's own eshkol_matcher module."""
    if not os.path.exists(paths.ESHKOL_MATCHER_PY):
        pytest.skip("eshkol_matcher.py is missing")
    return eshkol_lib.load_matcher()


@pytest.fixture(scope="session")
def matcher(matcher_module):
    """An EshkolMatcher built on the committed mapping workbook."""
    if not os.path.exists(paths.ESHKOL_MAPPING_XLSX):
        pytest.skip("eshkol_mapping.xlsx is missing")
    return matcher_module.EshkolMatcher(paths.ESHKOL_MAPPING_XLSX)
