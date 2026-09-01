"""Part A — the CBS 2024 figures the dashboard publishes.

Every rule checked here is one CLAUDE.md states as load-bearing: the cluster is
exactly the two sub-districts, people-weighted aggregation, the national average
that is easy to confuse with a different series, and the suppression floor.
"""

import pytest

# CLAUDE.md · "18 הרשויות" — the cluster's membership, in the source's spelling.
EXPECTED_AUTHORITIES = {
    "ראש פינה", "יסוד המעלה", "מטולה", "ג'ש (גוש חלב)", "טובא-זנגרייה",
    "חצור הגלילית", "קריית שמונה", "הגליל העליון", "מרום הגליל", "מבואות החרמון",
    "צפת", "בוקעאתא", "קצרין", "מג'דל שמס", "מסעדה", "ע'ג'ר", "עין קנייא", "גולן",
}
CLUSTER_WORKERS = 83_774          # CLAUDE.md — the anchor that defines the cluster
NATIONAL_SALARY = 12_975.83       # CLAUDE.md pitfall 1 — not 13,514, a different series
SUPPRESSION_FLOOR = 10            # CLAUDE.md pitfall 5
ROUNDING = 0.01                   # data.json publishes salaries to two decimals


def _weighted(items, field):
    total = sum(item["workers"] for item in items)
    return sum(item["workers"] * item[field] for item in items) / total


# --- the cluster's membership --------------------------------------------------

def test_should_publish_exactly_the_eighteen_cluster_authorities(data):
    # Arrange
    published = {item["name"] for item in data["authorities"]["items"]}

    # Act / Assert
    assert published == EXPECTED_AUTHORITIES, (
        f"missing: {sorted(EXPECTED_AUTHORITIES - published)} · "
        f"unexpected: {sorted(published - EXPECTED_AUTHORITIES)}"
    )


def test_should_assign_every_authority_to_a_sub_district(data):
    # Arrange / Act
    unassigned = [
        item["name"] for item in data["authorities"]["items"] if not item.get("nafa")
    ]

    # Assert
    assert unassigned == [], f"authorities with no sub-district: {unassigned}"


def test_should_name_every_authority_uniquely(data):
    # Arrange
    names = [item["name"] for item in data["authorities"]["items"]]

    # Act / Assert
    assert len(set(names)) == len(names), f"duplicate authority rows: {names}"


# --- the anchor: 18 authorities == Safed + Golan sub-districts -----------------

def test_should_total_the_cluster_to_the_published_anchor(data):
    """CLAUDE.md: the 18 authorities sum to 83,774 employees. That is the anchor."""
    # Arrange
    items = data["authorities"]["items"]

    # Act
    total = sum(item["workers"] for item in items)

    # Assert
    assert total == CLUSTER_WORKERS, f"the cluster totals {total:,}, not {CLUSTER_WORKERS:,}"
    assert data["authorities"]["region"]["workers"] == total, (
        "the region card disagrees with the sum of its authorities"
    )


def test_should_reconcile_the_authorities_with_the_two_sub_districts(data):
    """The 18 authorities are exactly Safed + Golan — the claim the anchor rests on."""
    # Arrange
    authorities = sum(item["workers"] for item in data["authorities"]["items"])

    # Act
    sub_districts = sum(nafa["workers"] for nafa in data["authorities"]["nafot"])

    # Assert
    assert authorities == sub_districts, (
        f"authorities total {authorities:,} but the sub-districts total {sub_districts:,} — "
        "the cluster is no longer equal to Safed + Golan"
    )


# --- the weighting rule --------------------------------------------------------

@pytest.mark.parametrize("field", ["salary", "months"])
def test_should_weight_the_region_average_by_people_not_by_authorities(data, field):
    """CLAUDE.md · כלל השקלול — groups of people combine weighted by headcount."""
    # Arrange
    items = data["authorities"]["items"]
    published = data["authorities"]["region"][field]

    # Act
    weighted = _weighted(items, field)
    simple = sum(item[field] for item in items) / len(items)

    # Assert
    assert abs(weighted - published) <= ROUNDING, (
        f"region {field} {published} is not the people-weighted mean {weighted:.4f}"
    )
    assert abs(simple - published) > ROUNDING, (
        f"region {field} coincides with an unweighted mean — the weighting rule is "
        "not observable in this figure, so this test would not catch its loss"
    )


# --- the national reference point ---------------------------------------------

def test_should_publish_the_per_person_national_average_not_the_per_post_series(data):
    """CLAUDE.md pitfall 1: 13,514 is wages per salaried post, a different series."""
    # Arrange / Act
    published = data["authorities"]["national"]["salary"]

    # Assert
    assert published == NATIONAL_SALARY, (
        f"the national average is {published}, not the per-person {NATIONAL_SALARY}"
    )


def test_should_place_the_cluster_below_the_national_average(data):
    # Arrange
    region = data["authorities"]["region"]["salary"]
    national = data["authorities"]["national"]["salary"]

    # Act / Assert
    assert region < national, (
        f"the cluster average {region} is no longer below the national {national} — "
        "verify against the source before publishing"
    )


# --- per-authority figures -----------------------------------------------------

def test_should_publish_positive_headcount_and_wage_for_every_authority(data):
    # Arrange / Act
    offenders = [
        (item["name"], item["workers"], item["salary"], item["months"])
        for item in data["authorities"]["items"]
        if item["workers"] <= 0 or item["salary"] <= 0 or not 0 < item["months"] <= 12
    ]

    # Assert
    assert offenders == [], f"implausible authority rows: {offenders}"


def test_should_keep_every_authority_headcount_above_the_suppression_floor(data):
    # Arrange / Act
    below = [
        (item["name"], item["workers"])
        for item in data["authorities"]["items"]
        if item["workers"] < SUPPRESSION_FLOOR
    ]

    # Assert
    assert below == [], f"authorities published below the suppression floor: {below}"


# --- the industry breakdown ----------------------------------------------------

def test_should_publish_the_fifty_one_industry_groups(data):
    # Arrange / Act / Assert
    assert len(data["anafim"]) == 51, f"{len(data['anafim'])} industry groups, expected 51"


def test_should_label_and_place_every_industry_group(data):
    # Arrange / Act
    incomplete = [
        group.get("code")
        for group in data["anafim"]
        if not group.get("label") or not group.get("seder") or not group.get("code")
    ]

    # Assert
    assert incomplete == [], f"industry groups missing a code, label or order: {incomplete}"


def test_should_give_every_industry_group_a_national_and_a_regional_reading(data):
    # Arrange / Act
    missing = [group["code"] for group in data["anafim"] if "nat" not in group or "reg" not in group]

    # Assert
    assert missing == [], f"industry groups without both readings: {missing}"


def test_should_derive_industry_coverage_from_the_headcounts_it_reports(data):
    """coverage is a ratio the page prints; it must be the ratio of its own parts."""
    # Arrange
    wrong = []

    # Act
    for name, block in data["anafByAuth"].items():
        expected = round(block["workers"] / block["of"], 4)
        if abs(expected - block["coverage"]) > 1e-4:
            wrong.append((name, block["coverage"], expected))
        if block["anafim"] != len(block["cells"]):
            wrong.append((name, "cell count", block["anafim"], len(block["cells"])))

    # Assert
    assert wrong == [], f"industry coverage does not match its own headcounts: {wrong}"


def test_should_never_cover_more_workers_than_the_authority_employs(data):
    # Arrange / Act
    over = [
        (name, block["workers"], block["of"])
        for name, block in data["anafByAuth"].items()
        if block["workers"] > block["of"]
    ]

    # Assert
    assert over == [], f"industry coverage exceeds the authority's headcount: {over}"


# --- the 2022 -> 2024 comparison ----------------------------------------------

def test_should_declare_the_suppression_floor_the_sources_use(data):
    # Arrange / Act / Assert
    assert data["change"]["floor"] == SUPPRESSION_FLOOR, (
        f"the suppression floor is {data['change']['floor']}, not {SUPPRESSION_FLOOR}; "
        "CLAUDE.md pitfall 5 says the 2022 figures depend on it"
    )


def test_should_derive_the_2022_coverage_from_the_workers_it_could_not_see(data):
    # Arrange
    change = data["change"]

    # Act
    expected = round(change["workers"] / (change["workers"] + change["maxMissing"]), 4)

    # Assert
    assert abs(expected - change["coverage"]) <= 1e-4, (
        f"2022 coverage {change['coverage']} is not {expected} from "
        f"{change['workers']:,} covered and up to {change['maxMissing']:,} suppressed"
    )


def test_should_compare_the_same_authorities_across_both_years(data):
    # Arrange
    compared = set(data["change"]["byAuthority"])

    # Act / Assert
    assert compared == EXPECTED_AUTHORITIES, (
        f"the 2022→2024 comparison covers {len(compared)} authorities, not the 18: "
        f"missing {sorted(EXPECTED_AUTHORITIES - compared)}"
    )


# --- the definitions the footer prints ----------------------------------------

def test_should_carry_the_three_definitions_lifted_from_the_source_sheet(data):
    """CLAUDE.md: the definitions are quoted from 'מידע נילווה', never written in code."""
    # Arrange
    definitions = data["meta"]["definitions"]

    # Act / Assert
    assert len(definitions) == 3, f"{len(definitions)} definitions, expected 3"
    assert all(item.get("term") and item.get("text") for item in definitions), (
        f"a definition is missing its term or its text: {definitions}"
    )
    assert data["meta"]["sheet"] == "מידע נילווה", (
        "the definitions no longer declare the source sheet they were taken from"
    )
