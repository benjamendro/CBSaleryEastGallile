"""Cell-level verification of the 2022 comparison and the 2016–2022 trend.

Both blocks are computed rather than copied, so each test restates the documented
rule and applies it to the source cells independently:

  * 2022 is aggregated from the *industry-order* level, because the suppression
    floor loses 5.2% of employees at the two-digit level (CLAUDE.md pitfall 5).
  * The National Insurance cluster row in the workbook is wrong — its wage column
    is an unweighted mean of the two sub-districts (pitfall 4) — so the trend must
    be rebuilt from those two rows, weighted by headcount.
"""

import pytest

from _lib import sources

SALARY_PLACES = 2   # data.json publishes the 2022 wages to two decimals
TREND_PLACES = 1    # and the trend wages to one


@pytest.fixture(scope="module")
def orders_2022():
    return sources.cbs_2022_by_seder()


@pytest.fixture(scope="module")
def table8():
    return {
        "sub_districts": sources.btl_table8_sub_districts(),
        "national": sources.btl_table8_national(),
        "cluster_row": sources.btl_table8_cluster_row(),
    }


# --- the 2022 comparison -------------------------------------------------------

def test_should_compare_exactly_the_authorities_the_2022_workbook_covers(data, orders_2022):
    # Arrange / Act
    published = set(data["change"]["byAuthority"])

    # Assert
    assert published == set(orders_2022), (
        f"only in data.json: {sorted(published - set(orders_2022))} · "
        f"only in the workbook: {sorted(set(orders_2022) - published)}"
    )


def test_should_sum_the_2022_headcount_over_every_industry_order(data, orders_2022):
    """Including the unclassified '*' row — dropping it would understate every authority."""
    # Arrange
    mismatches = []

    # Act
    for authority, published in data["change"]["byAuthority"].items():
        expected = sum(cell["workers"] for cell in orders_2022[authority].values())
        if published["workers"] != expected:
            mismatches.append((authority, published["workers"], expected))

    # Assert
    assert mismatches == [], f"2022 headcounts that do not sum from the orders: {mismatches}"


def test_should_weight_the_2022_wage_by_headcount_across_the_orders(data, orders_2022):
    # Arrange
    mismatches = []

    # Act
    for authority, published in data["change"]["byAuthority"].items():
        cells = orders_2022[authority].values()
        expected = round(
            sources.weighted([(cell["workers"], cell["salary"]) for cell in cells]),
            SALARY_PLACES,
        )
        if published["salary"] != expected:
            mismatches.append((authority, published["salary"], expected))

    # Assert
    assert mismatches == [], f"2022 wages that are not the weighted mean: {mismatches}"


def test_should_count_the_industry_orders_each_authority_actually_has(data, orders_2022):
    # Arrange / Act
    mismatches = [
        (authority, published["sections"], len(orders_2022[authority]))
        for authority, published in data["change"]["byAuthority"].items()
        if published["sections"] != len(orders_2022[authority])
    ]

    # Assert
    assert mismatches == [], f"published order counts that are not the workbook's: {mismatches}"


def test_should_total_the_2022_cells_the_workbook_holds(data, orders_2022):
    # Arrange / Act
    present = sum(len(cells) for cells in orders_2022.values())

    # Assert
    assert data["change"]["cells"] == present, (
        f"data.json counts {data['change']['cells']} cells, the workbook holds {present}"
    )


def test_should_total_the_2022_headcount_across_the_cluster(data):
    # Arrange / Act
    summed = sum(item["workers"] for item in data["change"]["byAuthority"].values())

    # Assert
    assert data["change"]["workers"] == summed, (
        f"the 2022 cluster total is {data['change']['workers']:,}, its authorities sum "
        f"to {summed:,}"
    )


def test_should_bound_the_suppressed_2022_employees_by_the_floor(data, orders_2022):
    """Each absent authority×order cell can hide at most floor-1 employees."""
    # Arrange
    authorities = len(orders_2022)
    orders = {order for cells in orders_2022.values() for order in cells}
    present = sum(len(cells) for cells in orders_2022.values())

    # Act
    absent = len(orders) * authorities - present
    expected = absent * (data["change"]["floor"] - 1)

    # Assert
    assert data["change"]["maxMissing"] == expected, (
        f"the published bound is {data['change']['maxMissing']}, but {absent} absent cells "
        f"× {data['change']['floor'] - 1} employees gives {expected}"
    )


# --- the 2016–2022 National Insurance trend ------------------------------------

def test_should_cover_the_years_table_eight_publishes(data):
    # Arrange / Act
    published = [int(row["year"]) for row in data["btl"]["rows"]]

    # Assert
    assert published == sources.BTL_YEARS, (
        f"the trend covers {published}, table 8 covers {sources.BTL_YEARS}"
    )


def test_should_sum_the_cluster_headcount_from_the_two_sub_district_rows(data, table8):
    # Arrange
    mismatches = []

    # Act
    for row in data["btl"]["rows"]:
        year = int(row["year"])
        expected = sum(table8["sub_districts"][name][year][0] for name in ("צפת", "גולן"))
        if row["workers"] != expected:
            mismatches.append((year, row["workers"], expected))

    # Assert
    assert mismatches == [], f"trend headcounts that are not Safed + Golan: {mismatches}"


def test_should_recompute_the_cluster_wage_as_a_weighted_mean(data, table8):
    """CLAUDE.md pitfall 4 — the workbook's own row must not be copied."""
    # Arrange
    mismatches = []

    # Act
    for row in data["btl"]["rows"]:
        year = int(row["year"])
        pairs = [table8["sub_districts"][name][year] for name in ("צפת", "גולן")]
        expected = round(sources.weighted(pairs), TREND_PLACES)
        if row["salary"] != expected:
            mismatches.append((year, row["salary"], expected))

    # Assert
    assert mismatches == [], f"trend wages that are not the weighted mean: {mismatches}"


def test_should_not_copy_the_workbooks_own_cluster_wage(data, table8):
    """The row exists and is wrong; publishing it would lower every year by ~1.5%."""
    # Arrange
    copied = []

    # Act
    for row in data["btl"]["rows"]:
        year = int(row["year"])
        if row["salary"] == round(table8["cluster_row"][year][1], TREND_PLACES):
            copied.append(year)

    # Assert
    assert copied == [], (
        f"the trend wage for {copied} equals the workbook's own East Galilee row, which "
        "averages the two sub-districts without weighting them"
    )


def test_should_confirm_the_workbook_row_is_the_unweighted_mean_it_is_documented_to_be(
    table8,
):
    """Pins the reason the recomputation exists, so the rule cannot lose its basis."""
    # Arrange
    unexplained = []

    # Act
    for year in sources.BTL_YEARS:
        simple = sum(table8["sub_districts"][name][year][1] for name in ("צפת", "גולן")) / 2
        if abs(table8["cluster_row"][year][1] - simple) > 0.05:
            unexplained.append((year, table8["cluster_row"][year][1], simple))

    # Assert
    assert unexplained == [], (
        "the workbook's East Galilee wage is no longer the unweighted mean of the two "
        f"sub-districts: {unexplained}. Re-examine whether the recomputation is still right."
    )


@pytest.mark.parametrize("field, column", [("national", 1), ("nationalWorkers", 0)])
def test_should_copy_the_national_reference_from_table_eight(data, table8, field, column):
    # Arrange
    mismatches = []

    # Act
    for row in data["btl"]["rows"]:
        expected = table8["national"][int(row["year"])][column]
        if row[field] != expected:
            mismatches.append((row["year"], row[field], expected))

    # Assert
    assert mismatches == [], f"trend {field} values that are not table 8's: {mismatches}"
