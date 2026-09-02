"""Cell-level verification of part A: does data.json say what the workbook says?

test_pipeline_traceability.py proves data.json is what build_data.py produces.
That is determinism, not correctness: a reader pointed at the wrong column would
be wrong the same way every time. These tests read the workbook independently —
sheet by sheet, row by row, with no pipeline code in the loop — and compare every
published figure with the cell it claims to come from.
"""

import pytest

from _lib import sources

DECIMALS = 4  # data.json publishes months and wages to four decimal places


def _round(value):
    return None if value is None else round(value, DECIMALS)


@pytest.fixture(scope="module")
def workbook():
    authorities, sub_districts, national = sources.cbs_authorities()
    return {"authorities": authorities, "sub_districts": sub_districts, "national": national}


# --- the authority rows --------------------------------------------------------

def test_should_publish_exactly_the_authorities_the_workbook_lists(data, workbook):
    # Arrange
    published = {item["name"] for item in data["authorities"]["items"]}

    # Act
    in_source = set(workbook["authorities"])

    # Assert
    assert published == in_source, (
        f"only in data.json: {sorted(published - in_source)} · "
        f"only in the workbook: {sorted(in_source - published)}"
    )


@pytest.mark.parametrize("field", ["workers", "months", "salary"])
def test_should_copy_every_authority_figure_from_its_cell(data, workbook, field):
    # Arrange
    mismatches = []

    # Act
    for item in data["authorities"]["items"]:
        cell = workbook["authorities"][item["name"]][field]
        expected = cell if field == "workers" else _round(cell)
        if item[field] != expected:
            mismatches.append((item["name"], field, item[field], expected))

    # Assert
    assert mismatches == [], f"published figures that are not the workbook's: {mismatches}"


# --- the two sub-district rows -------------------------------------------------

def test_should_publish_the_two_sub_district_rows_the_workbook_holds(data, workbook):
    # Arrange
    published = {nafa["name"] for nafa in data["authorities"]["nafot"]}

    # Act / Assert
    assert published == set(workbook["sub_districts"]), (
        f"data.json publishes {sorted(published)}, the workbook holds "
        f"{sorted(workbook['sub_districts'])}"
    )


@pytest.mark.parametrize("field", ["workers", "months", "salary"])
def test_should_copy_every_sub_district_figure_from_its_cell(data, workbook, field):
    # Arrange
    mismatches = []

    # Act
    for nafa in data["authorities"]["nafot"]:
        cell = workbook["sub_districts"][nafa["name"]][field]
        expected = cell if field == "workers" else _round(cell)
        if nafa[field] != expected:
            mismatches.append((nafa["name"], field, nafa[field], expected))

    # Assert
    assert mismatches == [], f"sub-district figures that are not the workbook's: {mismatches}"


# --- the sub-district assignment, which the workbook does not state ------------

def test_should_assign_authorities_to_sub_districts_so_the_totals_reconcile(data, workbook):
    """The sheet never says which authority sits in which sub-district.

    That mapping is the pipeline's own knowledge, so it cannot be read off a cell.
    What can be checked is the consequence: the authorities the dashboard assigns
    to each sub-district must add up to that sub-district's published headcount.
    A single authority filed under the wrong sub-district breaks both totals.
    """
    # Arrange
    totals = {}

    # Act
    for item in data["authorities"]["items"]:
        totals[item["nafa"]] = totals.get(item["nafa"], 0) + item["workers"]

    # Assert
    for name, published in workbook["sub_districts"].items():
        assert totals.get(name) == published["workers"], (
            f"{name}: the authorities assigned to it total {totals.get(name):,} but the "
            f"workbook's own row says {published['workers']:,}"
        )


def test_should_reproduce_each_sub_district_wage_from_its_own_authorities(data, workbook):
    """A stronger form of the same check: the weighted wage must also reconcile."""
    # Arrange
    groups = {}

    # Act
    for item in data["authorities"]["items"]:
        groups.setdefault(item["nafa"], []).append((item["workers"], item["salary"]))

    # Assert
    for name, published in workbook["sub_districts"].items():
        rebuilt = sources.weighted(groups[name])
        assert abs(rebuilt - published["salary"]) < 0.5, (
            f"{name}: its authorities imply a wage of {rebuilt:,.2f} but the workbook "
            f"row says {published['salary']:,.2f} — an authority is filed under the "
            "wrong sub-district, or a wage is wrong"
        )


# --- the national reference row ------------------------------------------------

def test_should_scale_the_national_headcount_out_of_thousands(data, workbook):
    """Row 3 alone is published in thousands; every other row is in units."""
    # Arrange / Act
    published = data["authorities"]["national"]["workers"]

    # Assert
    assert published == workbook["national"]["workers"], (
        f"the national headcount is {published:,}, the workbook's row 3 gives "
        f"{workbook['national']['workers']:,}"
    )
    assert published > 4_000_000, (
        f"{published:,} looks like the unscaled 'thousands' figure, not a headcount"
    )


@pytest.mark.parametrize("field", ["months", "salary"])
def test_should_copy_the_national_average_from_its_cell(data, workbook, field):
    # Arrange / Act
    published = data["authorities"]["national"][field]

    # Assert
    assert published == _round(workbook["national"][field]), (
        f"national {field} is {published}, the workbook cell gives "
        f"{_round(workbook['national'][field])}"
    )


# --- the definitions the footer prints ----------------------------------------

def test_should_quote_the_definitions_word_for_word_from_the_source_sheet(data):
    """CLAUDE.md: the definitions are lifted from 'מידע נילווה', never written in code."""
    # Arrange
    in_sheet = sources.cbs_definitions()

    # Act
    mismatches = []
    for definition in data["meta"]["definitions"]:
        term = definition["term"].strip()
        expected = in_sheet.get(term)
        if expected is None:
            mismatches.append((term, "term not found in the source sheet"))
        elif definition["text"].strip() != expected:
            mismatches.append((term, definition["text"], expected))

    # Assert
    assert mismatches == [], f"definitions that are not the sheet's wording: {mismatches}"


def test_should_carry_every_definition_the_source_sheet_offers(data):
    # Arrange
    in_sheet = set(sources.cbs_definitions())

    # Act
    published = {definition["term"].strip() for definition in data["meta"]["definitions"]}

    # Assert
    assert published == in_sheet, (
        f"the sheet defines {sorted(in_sheet)} but the page publishes {sorted(published)}"
    )
