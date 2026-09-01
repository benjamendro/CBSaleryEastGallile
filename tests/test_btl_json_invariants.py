"""Part B — the National Insurance 2016–2024 figures the dashboard publishes.

The load-bearing rule here is CLAUDE.md pitfall 11: the appendices are a closed
partition, which is what lets 'סוג המבוטחים' be reconstructed for authorities the
source never publishes it for. If the partition stops holding, the reconstruction
is invented rather than derived.
"""

import pytest

YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
POPULATIONS = ("emp", "self", "all")

# CLAUDE.md pitfall 7 — the two authorities the source cannot cover.
EXPECTED_EXCLUSIONS = {"יסוד המעלה", "מטולה"}

# The national row is a separately published, rounded total; the cluster and the
# authorities are summed from the appendices and must reconcile exactly.
NATIONAL_ROUNDING_SLACK = 2


def _covered_authorities(btl):
    return [auth for auth in btl["authorities"] if not auth.get("missing")]


# --- shape ---------------------------------------------------------------------

def test_should_cover_the_nine_years_it_declares(btl):
    # Arrange / Act / Assert
    assert btl["meta"]["years"] == YEARS, f"years are {btl['meta']['years']}, expected {YEARS}"


def test_should_carry_the_three_populations_with_their_appendices(btl):
    # Arrange
    populations = {pop["id"]: pop for pop in btl["populations"]}

    # Act / Assert
    assert set(populations) == set(POPULATIONS), f"populations are {sorted(populations)}"
    for pop in populations.values():
        assert pop["appendix"], f"population {pop['id']} does not name its appendix"
        assert pop["parts"], f"population {pop['id']} does not name its component appendices"


def test_should_name_each_population_separately_from_how_it_is_counted(btl):
    """CLAUDE.md pitfall 14: 'כלל העובדים' cannot take a number in front of it."""
    # Arrange
    populations = {pop["id"]: pop for pop in btl["populations"]}

    # Act / Assert
    assert populations["all"]["label"] != populations["all"]["count"], (
        "the 'all workers' population uses one string for both its name and its "
        "countable form; pitfall 14 says those must differ"
    )
    assert populations["all"]["count"] == "עובדים", (
        f"the countable form is {populations['all']['count']!r}, expected 'עובדים'"
    )


@pytest.mark.parametrize("scope", ["cluster", "national"])
@pytest.mark.parametrize("group", ["n", "trend"])
def test_should_give_every_series_one_point_per_year(btl, scope, group):
    # Arrange
    block = btl[scope][group]

    # Act
    lengths = {pop: len(values) for pop, values in block.items()}

    # Assert
    assert set(lengths) == set(POPULATIONS), f"{scope}.{group} covers {sorted(lengths)}"
    assert all(length == len(YEARS) for length in lengths.values()), (
        f"{scope}.{group} series lengths {lengths} do not match {len(YEARS)} years"
    )


def test_should_publish_a_row_for_each_of_the_eighteen_authorities(btl):
    # Arrange / Act / Assert
    assert len(btl["authorities"]) == 18, f"{len(btl['authorities'])} authority rows, expected 18"


# --- the closed partition: א׳ = ד׳ + ז׳ + ח׳ -----------------------------------

def _partition_errors(name, block, years, slack=0.5):
    errors = []
    for year in years:
        mix = block.get("mix", {}).get(str(year))
        if not mix:
            continue
        index = years.index(year)
        expected = {
            "emp": mix["emp"] + mix["both"],      # ג׳ = ד׳ + ח׳
            "self": mix["self"] + mix["both"],    # ו׳ = ז׳ + ח׳
            "all": mix["emp"] + mix["self"] + mix["both"],  # א׳ = ד׳ + ז׳ + ח׳
        }
        for pop in POPULATIONS:
            published = block["n"][pop][index]
            if published is None:
                continue
            if abs(published - expected[pop]) > slack:
                errors.append((name, year, pop, published, expected[pop]))
    return errors


def test_should_reconstruct_every_authority_headcount_from_the_appendices(btl):
    """Zero deviation, per CLAUDE.md pitfall 11 — this is what licenses the rebuild."""
    # Arrange
    errors = []

    # Act
    for auth in _covered_authorities(btl):
        errors += _partition_errors(auth["name"], auth, YEARS)

    # Assert
    assert errors == [], f"the appendix partition does not close for: {errors}"


def test_should_reconstruct_the_cluster_headcount_from_the_appendices(btl):
    # Arrange / Act
    errors = _partition_errors("cluster", btl["cluster"], YEARS)

    # Assert
    assert errors == [], f"the cluster does not reconcile with its appendices: {errors}"


def test_should_reconcile_the_national_totals_within_the_sources_rounding(btl):
    """The national row is published pre-rounded, so it reconciles to within a person or two."""
    # Arrange / Act
    errors = _partition_errors("national", btl["national"], YEARS, slack=NATIONAL_ROUNDING_SLACK)

    # Assert
    assert errors == [], (
        f"national totals drift further than the source's rounding explains: {errors}"
    )


def test_should_never_count_more_employees_than_workers(btl):
    """Employees and self-employed are subsets of all workers, by construction."""
    # Arrange
    offenders = []

    # Act
    for scope, block in [("cluster", btl["cluster"]), ("national", btl["national"])] + [
        (auth["name"], auth) for auth in _covered_authorities(btl)
    ]:
        for index in range(len(YEARS)):
            everyone = block["n"]["all"][index]
            if everyone is None:
                continue
            for pop in ("emp", "self"):
                part = block["n"][pop][index]
                if part is not None and part > everyone:
                    offenders.append((scope, YEARS[index], pop, part, everyone))

    # Assert
    assert offenders == [], f"a sub-population outnumbers all workers: {offenders}"


# --- declared coverage gaps ----------------------------------------------------

def test_should_exclude_only_the_authorities_the_source_cannot_cover(btl):
    """CLAUDE.md pitfall 7 — the gap must be declared, never dropped silently."""
    # Arrange
    excluded = {item["name"] for item in btl["cluster"]["excluded"]}

    # Act / Assert
    assert excluded == EXPECTED_EXCLUSIONS, (
        f"the cluster excludes {sorted(excluded)}, expected {sorted(EXPECTED_EXCLUSIONS)}"
    )
    assert all(item.get("why") for item in btl["cluster"]["excluded"]), (
        "an exclusion is published without saying why"
    )


def test_should_build_the_cluster_from_the_authorities_it_can_cover(btl):
    # Arrange
    base = set(btl["cluster"]["base"])
    excluded = {item["name"] for item in btl["cluster"]["excluded"]}

    # Act
    named = {auth["name"] for auth in btl["authorities"]}

    # Assert
    assert base <= named, f"the cluster base names authorities that have no row: {base - named}"
    assert not base & excluded, f"an excluded authority is still in the base: {base & excluded}"
    assert len(base) == len(btl["authorities"]) - len(excluded), (
        f"the base holds {len(base)} of {len(btl['authorities'])} authorities minus "
        f"{len(excluded)} exclusions"
    )


def test_should_flag_the_authority_with_no_data_as_missing(btl):
    # Arrange / Act
    flagged = {auth["name"] for auth in btl["authorities"] if auth.get("missing")}

    # Assert
    assert flagged, "no authority is flagged missing, yet the cluster declares exclusions"
    assert flagged <= EXPECTED_EXCLUSIONS, f"unexpected authorities flagged missing: {flagged}"
    for auth in btl["authorities"]:
        if auth.get("missing"):
            assert "mix" not in auth, (
                f"{auth['name']} is flagged missing but still carries a breakdown"
            )


# --- plausibility of the published values -------------------------------------

def test_should_publish_non_negative_headcounts_everywhere(btl):
    # Arrange
    offenders = []

    # Act
    for scope, block in [("cluster", btl["cluster"]), ("national", btl["national"])] + [
        (auth["name"], auth) for auth in _covered_authorities(btl)
    ]:
        for pop, series in block["n"].items():
            for index, value in enumerate(series):
                if value is not None and value < 0:
                    offenders.append((scope, pop, YEARS[index], value))

    # Assert
    assert offenders == [], f"negative headcounts: {offenders}"


def test_should_publish_wages_within_a_plausible_band(btl):
    # Arrange
    offenders = []

    # Act
    for scope, block in [("cluster", btl["cluster"]), ("national", btl["national"])] + [
        (auth["name"], auth) for auth in _covered_authorities(btl)
    ]:
        for pop, series in block["trend"].items():
            for index, value in enumerate(series):
                if value is not None and not 1_000 <= value <= 60_000:
                    offenders.append((scope, pop, YEARS[index], value))

    # Assert
    assert offenders == [], f"monthly wages outside a plausible 1,000–60,000 ₪ band: {offenders}"
