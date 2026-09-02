"""Cell-level verification of part B against the National Insurance workbooks.

btl.json is assembled from six appendix tables in two editions, at two geography
levels — the locality tables for the fourteen localities and the regional-council
tables for the four councils. These tests open those workbooks directly and check
every published headcount, wage and median against the cell it came from.

The authority names differ between the sources: btl.json labels rows with the
'שם רשמי בלמס' column of eshkol_mapping.xlsx, while the tables use the National
Insurance spelling. The bridge is declared here explicitly rather than guessed at
run time, which is what CLAUDE.md's approved fix asks the mapping workbook to do.
"""

import pytest

from _lib import sources

YEARS = sources.BTL_OLD_YEARS + sources.BTL_NEW_YEARS

# btl.json's label -> the name the National Insurance tables use.
NAME_BRIDGE = {
    "קרית שמונה": "קריית שמונה",
    "טובא-זנגריה": "טובא-זנגרייה",
    "ג'ש )גוש חלב(": "ג'ש (גוש חלב)",
    "הגולן": "גולן",
}

# btl.json's mix keys are the appendices they are read from.
MIX_APPENDIX = {"emp": "ד", "self": "ז", "both": "ח"}
# and its populations are the appendices that publish each one's wages.
POPULATION_APPENDIX = {"emp": "ג", "self": "ו", "all": "א"}


def _table_name(published_name):
    return NAME_BRIDGE.get(published_name, published_name)


def _edition_of(year):
    return "new" if year in sources.BTL_NEW_YEARS else "old"


@pytest.fixture(scope="module")
def tables(btl_tables):
    """Every appendix table this module reads, loaded once."""
    loaded = {}
    for edition in ("new", "old"):
        for appendix in set(MIX_APPENDIX.values()) | set(POPULATION_APPENDIX.values()):
            for is_council in (False, True):
                loaded[(edition, appendix, is_council)] = sources.btl_table_for(
                    btl_tables, appendix, edition, is_council
                )
    return loaded


def _row_for(tables, authority, appendix, year):
    edition = _edition_of(year)
    rows = tables[(edition, appendix, authority["rc"])]
    return rows.get(_table_name(authority["name"]))


def _covered(btl):
    return [auth for auth in btl["authorities"] if not auth.get("missing")]


# --- the name bridge itself ----------------------------------------------------

def test_should_find_every_covered_authority_in_the_source_tables(btl, tables):
    # Arrange
    rows = tables[("new", "ד", False)], tables[("new", "ד", True)]

    # Act
    unfound = [
        auth["name"]
        for auth in _covered(btl)
        if _table_name(auth["name"]) not in rows[1 if auth["rc"] else 0]
    ]

    # Assert
    assert unfound == [], f"authorities the National Insurance tables do not contain: {unfound}"


def test_should_flag_as_missing_exactly_the_authority_the_tables_omit(btl, tables):
    """CLAUDE.md pitfall 7 — the locality tables cover 2,000+ residents only."""
    # Arrange
    localities = tables[("new", "ד", False)]
    councils = tables[("new", "ד", True)]

    # Act
    absent = {
        auth["name"]
        for auth in btl["authorities"]
        if _table_name(auth["name"]) not in (councils if auth["rc"] else localities)
    }
    flagged = {auth["name"] for auth in btl["authorities"] if auth.get("missing")}

    # Assert
    assert absent == flagged, (
        f"absent from the tables: {sorted(absent)} · flagged missing: {sorted(flagged)}"
    )


# --- the employment mix: appendices ד, ז and ח ---------------------------------

@pytest.mark.parametrize("part", sorted(MIX_APPENDIX))
def test_should_copy_every_employment_mix_headcount_from_its_appendix(btl, tables, part):
    # Arrange
    appendix = MIX_APPENDIX[part]
    mismatches = []

    # Act
    for auth in _covered(btl):
        for year in YEARS:
            published = auth["mix"].get(str(year), {}).get(part)
            row = _row_for(tables, auth, appendix, year)
            expected = None if row is None else sources.btl_value(
                row, _edition_of(year), "workers", year
            )
            if published != expected:
                mismatches.append((auth["name"], year, part, published, expected))

    # Assert
    assert mismatches == [], (
        f"mix figures that are not appendix {appendix}'s: {mismatches[:15]}"
    )


# --- the wage trend: appendices ג, ו and א -------------------------------------

@pytest.mark.parametrize("population", sorted(POPULATION_APPENDIX))
def test_should_copy_every_wage_in_the_trend_from_its_appendix(btl, tables, population):
    # Arrange
    appendix = POPULATION_APPENDIX[population]
    mismatches = []

    # Act
    for auth in _covered(btl):
        for index, year in enumerate(YEARS):
            published = auth["trend"][population][index]
            row = _row_for(tables, auth, appendix, year)
            expected = None if row is None else sources.btl_value(
                row, _edition_of(year), "mean_work", year
            )
            if published != expected:
                mismatches.append((auth["name"], year, population, published, expected))

    # Assert
    assert mismatches == [], (
        f"trend wages that are not appendix {appendix}'s: {mismatches[:15]}"
    )


def test_should_publish_the_wage_per_month_worked_it_declares(btl):
    # Arrange / Act / Assert
    assert btl["meta"]["measure"] == "שכר ממוצע לחודש עבודה", (
        f"the declared measure changed to {btl['meta']['measure']!r}; the trend tests "
        "read the 'ממוצע לחודש עבודה' columns and would now be reading the wrong block"
    )


# --- the medians, which exist for the newer edition only -----------------------

@pytest.mark.parametrize("population", sorted(POPULATION_APPENDIX))
def test_should_copy_every_median_from_its_appendix(btl, tables, population):
    # Arrange
    appendix = POPULATION_APPENDIX[population]
    mismatches = []

    # Act
    for auth in _covered(btl):
        for year in sources.BTL_NEW_YEARS:
            published = auth["median"].get(population, {}).get(str(year))
            row = _row_for(tables, auth, appendix, year)
            expected = None if row is None else sources.btl_value(
                row, "new", "median_work", year
            )
            if published != expected:
                mismatches.append((auth["name"], year, population, published, expected))

    # Assert
    assert mismatches == [], f"medians that are not appendix {appendix}'s: {mismatches[:15]}"


def test_should_publish_medians_only_for_the_years_the_source_has_them(btl):
    """CLAUDE.md — medians exist for 2023–2024 only; an older one would be invented."""
    # Arrange
    allowed = {str(year) for year in sources.BTL_NEW_YEARS}

    # Act
    extra = [
        (auth["name"], population, sorted(set(values) - allowed))
        for auth in _covered(btl)
        for population, values in auth["median"].items()
        if set(values) - allowed
    ]

    # Assert
    assert extra == [], f"medians published for years the source does not cover: {extra}"


# --- the national row ----------------------------------------------------------

@pytest.mark.parametrize("population", sorted(POPULATION_APPENDIX))
def test_should_copy_the_national_wage_trend_from_the_right_total(btl, btl_tables, population):
    """The national reference is not one row in one table.

    For 2023–2024 the locality table's 'סה"כ' row is the country total. For
    2016–2022 that row covers only localities of 2,000+ residents and understates
    the country by 1–2%, so the figure has to come from the district tables — which
    carry their own table numbers, a case of CLAUDE.md pitfall 9.
    """
    # Arrange
    appendix = POPULATION_APPENDIX[population]
    mismatches = []

    # Act
    for index, year in enumerate(YEARS):
        published = btl["national"]["trend"][population][index]
        expected = sources.btl_national_wage(btl_tables, appendix, year)
        if published != expected:
            mismatches.append((year, population, published, expected))

    # Assert
    assert mismatches == [], f"national trend wages that are not the source's: {mismatches}"


def test_should_not_mistake_the_partial_totals_row_for_the_country(btl, btl_tables):
    """Guards the distinction above: the two totals must stay measurably apart."""
    # Arrange
    rows = sources.btl_table_for(btl_tables, "א", "old", False)
    partial = next(row for name, row in rows.items() if name.startswith('סה"כ'))

    # Act
    coincidences = [
        year
        for year in sources.BTL_OLD_YEARS
        if btl["national"]["trend"]["all"][YEARS.index(year)]
        == sources.btl_value(partial, "old", "mean_work", year)
    ]

    # Assert
    assert coincidences == [], (
        f"the national wage for {coincidences} equals the localities-only total, which "
        "excludes every settlement under 2,000 residents"
    )


# --- the cluster is a sum of its authorities, never a table row ----------------

def test_should_build_the_cluster_headcount_from_its_own_authorities(btl):
    # Arrange
    base = set(btl["cluster"]["base"])
    mismatches = []

    # Act
    for year in YEARS:
        for part in MIX_APPENDIX:
            published = btl["cluster"]["mix"].get(str(year), {}).get(part)
            summed = sum(
                auth["mix"][str(year)][part]
                for auth in btl["authorities"]
                if auth["name"] in base and str(year) in auth.get("mix", {})
            )
            if published is not None and abs(published - summed) > 0.5:
                mismatches.append((year, part, published, summed))

    # Assert
    assert mismatches == [], (
        f"the cluster headcount is not the sum of the authorities in its base: {mismatches}"
    )


# --- the wage distribution ------------------------------------------------------

@pytest.mark.parametrize("population", sorted(POPULATION_APPENDIX))
def test_should_copy_every_distribution_band_from_the_income_group_table(
    btl, btl_tables, population
):
    """Seven bands per authority per year, read from the income-group tables."""
    # Arrange
    appendix = POPULATION_APPENDIX[population]
    mismatches = []
    rows = {
        is_council: sources.btl_income_rows(btl_tables, appendix, is_council)
        for is_council in (False, True)
    }

    # Act
    for auth in _covered(btl):
        row = rows[auth["rc"]].get(_table_name(auth["name"]))
        for year in btl["meta"]["distYears"]:
            published = auth["dist"].get(population, {}).get(str(year))
            expected = None if row is None else sources.btl_income_bands(row, year)
            if published != expected:
                mismatches.append((auth["name"], year, population, published, expected))

    # Assert
    assert mismatches == [], (
        f"distribution bands that are not the income table's: {mismatches[:10]}"
    )


def test_should_publish_seven_distribution_bands_that_account_for_everyone(btl):
    """The bands partition the population, so each year's shares total 100%."""
    # Arrange
    offenders = []

    # Act
    for auth in _covered(btl):
        for population, years in auth["dist"].items():
            for year, bands in years.items():
                if len(bands) != sources.BTL_INCOME_BANDS:
                    offenders.append((auth["name"], population, year, len(bands)))
                elif abs(sum(bands) - 100.0) > 0.35:
                    offenders.append((auth["name"], population, year, sum(bands)))

    # Assert
    assert offenders == [], f"distribution bands that do not account for 100%: {offenders}"


def test_should_publish_the_distribution_only_for_the_years_the_source_covers(btl):
    # Arrange
    allowed = {str(year) for year in btl["meta"]["distYears"]}

    # Act
    extra = [
        (auth["name"], population, sorted(set(years) - allowed))
        for auth in _covered(btl)
        for population, years in auth["dist"].items()
        if set(years) - allowed
    ]

    # Assert
    assert extra == [], f"distribution published for uncovered years: {extra}"


def test_should_survive_the_line_break_the_source_writes_inside_one_council_name(
    btl_tables,
):
    """Pins a defect in the source workbooks, so a future reader cannot fall into it.

    Table 45 stores 'מבואות החרמון' with a newline inside the name. Every other
    table spells it normally. A reader that matches names literally silently drops
    that council from the wage distribution — and only there, which is exactly the
    kind of gap nobody notices.
    """
    # Arrange
    council = "מבואות החרמון"

    # Act
    income = sources.btl_income_rows(btl_tables, "ג", True)
    wages = sources.btl_table_for(btl_tables, "ג", "new", True)

    # Assert
    assert council in income, (
        "the income table no longer yields the council whose name carries a line "
        "break — check that whitespace is still being collapsed"
    )
    assert council in wages, f"{council} is missing from the wage table"
