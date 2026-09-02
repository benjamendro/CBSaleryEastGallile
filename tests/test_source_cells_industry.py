"""Cell-level verification of the industry figures.

Three separate claims are checked against three separate sources: the 51 group
readings against the CBS industry sheet, their names and orders against the CBS
industry dictionary, and the industry×authority breakdown against the
supplementary workbook. None of it goes through the pipeline's readers.
"""

import pytest

from _lib import sources

DECIMALS = 4
CELL_DECIMALS = 2  # the supplementary workbook publishes wages to two places


@pytest.fixture(scope="module")
def industry_sheet():
    return sources.cbs_industries()


@pytest.fixture(scope="module")
def dictionary():
    return sources.cbs_industry_dictionary()


@pytest.fixture(scope="module")
def by_authority():
    return sources.cbs_industry_by_authority()


# --- the 51 group readings -----------------------------------------------------

def test_should_publish_exactly_the_industry_groups_the_sheet_lists(data, industry_sheet):
    # Arrange
    published = {group["code"] for group in data["anafim"]}

    # Act / Assert
    assert published == set(industry_sheet), (
        f"only in data.json: {sorted(published - set(industry_sheet))} · "
        f"only in the sheet: {sorted(set(industry_sheet) - published)}"
    )


@pytest.mark.parametrize("scope", ["nat", "reg"])
@pytest.mark.parametrize("field", ["workers", "months", "salary"])
def test_should_copy_every_industry_reading_from_its_cell(data, industry_sheet, scope, field):
    # Arrange
    mismatches = []

    # Act
    for group in data["anafim"]:
        cell = industry_sheet[group["code"]][scope][field]
        expected = cell if field == "workers" else (None if cell is None else round(cell, DECIMALS))
        if group[scope].get(field) != expected:
            mismatches.append((group["code"], scope, field, group[scope].get(field), expected))

    # Assert
    assert mismatches == [], f"industry readings that are not the sheet's: {mismatches}"


def test_should_not_scale_the_industry_headcounts_despite_the_header(data, industry_sheet):
    """CLAUDE.md pitfall 3: cell C2 says '(באלפים)' and is wrong — these are counts."""
    # Arrange / Act
    total = sum(group["nat"]["workers"] for group in data["anafim"])

    # Assert
    assert total == 4_289_440, (
        f"the national industry headcounts total {total:,}; the documented full-count "
        "total is 4,289,440, so the '(באלפים)' header may have been believed"
    )


# --- names and orders come from the dictionary --------------------------------

def test_should_take_every_group_component_name_from_the_dictionary(data, dictionary):
    # Arrange
    mismatches = []

    # Act
    for group in data["anafim"]:
        expected = [dictionary[code][0] for code in group["code"].split("+")]
        if group["parts"] != expected:
            mismatches.append((group["code"], group["parts"], expected))

    # Assert
    assert mismatches == [], f"component names that are not the dictionary's: {mismatches}"


def test_should_name_the_order_of_every_group_from_the_dictionary(data, dictionary):
    """A group spanning two orders carries both, joined — never silently one."""
    # Arrange
    mismatches = []

    # Act
    for group in data["anafim"]:
        orders = []
        for code in group["code"].split("+"):
            order = dictionary[code][1]
            if order not in orders:
                orders.append(order)
        expected = " · ".join(orders)
        if group["seder"] != expected:
            mismatches.append((group["code"], group["seder"], expected))

    # Assert
    assert mismatches == [], f"industry orders that are not the dictionary's: {mismatches}"


def test_should_cover_every_two_digit_code_the_dictionary_knows_of_once(data, dictionary):
    """No code may be dropped from the grouping, and none may be counted twice."""
    # Arrange
    grouped = [code for group in data["anafim"] for code in group["code"].split("+")]

    # Act / Assert
    assert len(grouped) == len(set(grouped)), (
        f"a two-digit code appears in more than one group: "
        f"{sorted({c for c in grouped if grouped.count(c) > 1})}"
    )
    unknown = [code for code in grouped if code not in dictionary]
    assert unknown == [], f"grouped codes the dictionary does not define: {unknown}"


# --- the industry × authority breakdown ---------------------------------------

def test_should_break_down_exactly_the_authorities_the_workbook_covers(data, by_authority):
    # Arrange / Act
    published = set(data["anafByAuth"])

    # Assert
    assert published == set(by_authority), (
        f"only in data.json: {sorted(published - set(by_authority))} · "
        f"only in the workbook: {sorted(set(by_authority) - published)}"
    )


def test_should_carry_exactly_the_cells_the_workbook_holds_for_each_authority(
    data, by_authority
):
    # Arrange
    mismatches = []

    # Act
    for authority, block in data["anafByAuth"].items():
        expected = set(by_authority[authority])
        published = set(block["cells"])
        if published != expected:
            mismatches.append((authority, sorted(published ^ expected)))

    # Assert
    assert mismatches == [], f"industry cells that do not match the workbook's rows: {mismatches}"


@pytest.mark.parametrize("field", ["workers", "months", "salary"])
def test_should_copy_every_industry_by_authority_cell_from_the_workbook(
    data, by_authority, field
):
    # Arrange
    mismatches = []
    places = {"workers": None, "months": DECIMALS, "salary": CELL_DECIMALS}[field]

    # Act
    for authority, block in data["anafByAuth"].items():
        for code, cell in block["cells"].items():
            source_cell = by_authority[authority][code][field]
            expected = source_cell if places is None else round(source_cell, places)
            if cell[field] != expected:
                mismatches.append((authority, code, field, cell[field], expected))

    # Assert
    assert mismatches == [], f"cells that are not the workbook's: {mismatches[:20]}"


def test_should_sum_the_covered_headcount_from_the_cells_it_publishes(data):
    # Arrange
    mismatches = []

    # Act
    for authority, block in data["anafByAuth"].items():
        total = sum(cell["workers"] for cell in block["cells"].values())
        if total != block["workers"]:
            mismatches.append((authority, block["workers"], total))

    # Assert
    assert mismatches == [], f"covered headcount is not the sum of its cells: {mismatches}"


def test_should_measure_coverage_against_the_authority_the_main_sheet_reports(data):
    """The 'of' figure must be the authority's own headcount from part A."""
    # Arrange
    totals = {item["name"]: item["workers"] for item in data["authorities"]["items"]}

    # Act
    mismatches = [
        (authority, block["of"], totals.get(authority))
        for authority, block in data["anafByAuth"].items()
        if block["of"] != totals.get(authority)
    ]

    # Assert
    assert mismatches == [], (
        f"industry coverage is measured against the wrong denominator: {mismatches}"
    )
