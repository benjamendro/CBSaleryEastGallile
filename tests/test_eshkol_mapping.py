"""The mapping table, the skill that documents it, and the names the page prints.

eshkol_mapping.xlsx is the single source of truth for who belongs to the cluster.
SKILL.md restates that list in prose; the dashboard prints its own spellings. All
three have to agree, or a figure is attributed to the wrong authority — or the
same authority appears twice on one page under two names.
"""

import re

import pandas as pd
import pytest

from _lib import eshkol as eshkol_lib
from _lib import paths

EAST_COUNT, WEST_COUNT = 18, 19
CODE_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<code>\d{2,4})\)$")


def _skill_codes(section):
    """Parse 'נהריה (9100), עכו (7600), …' out of one SKILL.md cluster heading."""
    with open(paths.ESHKOL_SKILL_MD, encoding="utf-8") as handle:
        text = handle.read()
    block = text.split(f"**{section}:**")[1].split("\n\n")[0]
    codes = {}
    for item in block.split(","):
        # the first item trails the "בגליל … קיימות N רשויות" preamble line
        candidate = item.strip().splitlines()[-1].strip()
        match = CODE_RE.match(candidate)
        if match:
            codes[int(match.group("code"))] = match.group("name").strip()
    return codes


def _resolved_codes(matcher, names):
    frame = pd.DataFrame({"name": list(names)})
    result, _ = matcher.match_dataframe(frame, name_col="name")
    return {
        name: (int(code) if pd.notna(code) else None)
        for name, code in zip(result["name"], result["match_code"])
    }


# --- the mapping workbook itself ----------------------------------------------

def test_should_give_every_mapping_row_a_code_and_a_name(matcher):
    # Arrange
    targets = matcher.targets

    # Act
    incomplete = targets[targets["eshkol_name"].isna() | targets["code"].isna()]

    # Assert
    assert incomplete.empty, f"mapping rows without a code or a name:\n{incomplete}"


def test_should_keep_every_code_unique_across_the_mapping(matcher):
    """EshkolMatcher refuses to load a duplicated code, so this pins the guarantee."""
    # Arrange
    codes = matcher.targets["code"].tolist()

    # Act / Assert
    assert len(set(codes)) == len(codes), "duplicate codes survived into the target table"


def test_should_hold_the_two_clusters_at_their_documented_sizes(matcher):
    # Arrange / Act
    east = matcher.target_codes(eshkol_lib.AUTHORITY, eshkol_lib.EAST_GALILEE)
    west = matcher.target_codes(eshkol_lib.AUTHORITY, eshkol_lib.WEST_GALILEE)

    # Assert
    assert len(east) == EAST_COUNT, f"East Galilee has {len(east)} authorities, not {EAST_COUNT}"
    assert len(west) == WEST_COUNT, f"West Galilee has {len(west)} authorities, not {WEST_COUNT}"


# --- SKILL.md must not drift from the workbook --------------------------------

@pytest.mark.parametrize(
    "section, affiliation",
    [("גליל מזרחי", eshkol_lib.EAST_GALILEE), ("גליל מערבי", eshkol_lib.WEST_GALILEE)],
)
def test_should_list_the_same_codes_in_the_skill_as_in_the_workbook(
    matcher, section, affiliation
):
    # Arrange
    documented = set(_skill_codes(section))

    # Act
    mapped = set(matcher.target_codes(eshkol_lib.AUTHORITY, affiliation))

    # Assert
    assert documented == mapped, (
        f"{section}: SKILL.md and eshkol_mapping.xlsx disagree — "
        f"only in the doc: {sorted(documented - mapped)}, "
        f"only in the table: {sorted(mapped - documented)}"
    )


@pytest.mark.parametrize("section", ["גליל מזרחי", "גליל מערבי"])
def test_should_name_each_code_in_the_skill_as_the_workbook_names_it(matcher, section):
    # Arrange
    documented = _skill_codes(section)

    # Act
    disagreements = [
        (code, name, matcher.by_code[code]["eshkol_name"])
        for code, name in documented.items()
        if code in matcher.by_code
        and not matcher._name_matches_code(name, code)[0]
    ]

    # Assert
    assert disagreements == [], (
        f"{section}: SKILL.md names a code differently from the mapping: {disagreements}"
    )


# --- the dashboard's own authority names --------------------------------------

def test_should_resolve_every_part_a_authority_to_a_cluster_code(matcher, data):
    # Arrange
    names = [item["name"] for item in data["authorities"]["items"]]
    east = set(matcher.target_codes(eshkol_lib.AUTHORITY, eshkol_lib.EAST_GALILEE))

    # Act
    resolved = _resolved_codes(matcher, names)

    # Assert
    unresolved = [name for name, code in resolved.items() if code is None]
    assert unresolved == [], f"part A names no authority in the mapping recognises: {unresolved}"
    assert set(resolved.values()) == east, (
        "part A does not cover exactly the East Galilee cluster: "
        f"missing {sorted(east - set(resolved.values()))}"
    )


def test_should_resolve_every_part_b_authority_to_a_cluster_code(matcher, btl):
    # Arrange
    names = [auth["name"] for auth in btl["authorities"]]
    east = set(matcher.target_codes(eshkol_lib.AUTHORITY, eshkol_lib.EAST_GALILEE))

    # Act
    resolved = _resolved_codes(matcher, names)

    # Assert
    unresolved = [name for name, code in resolved.items() if code is None]
    assert unresolved == [], f"part B names no authority in the mapping recognises: {unresolved}"
    assert set(resolved.values()) == east, (
        "part B does not cover exactly the East Galilee cluster: "
        f"missing {sorted(east - set(resolved.values()))}"
    )


def test_should_attribute_both_parts_to_the_same_eighteen_authorities(matcher, data, btl):
    """Different spellings are survivable; different *authorities* are not."""
    # Arrange
    part_a = _resolved_codes(matcher, [item["name"] for item in data["authorities"]["items"]])
    part_b = _resolved_codes(matcher, [auth["name"] for auth in btl["authorities"]])

    # Act / Assert
    assert set(part_a.values()) == set(part_b.values()), (
        "the two halves of the page describe different sets of authorities"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN DEFECT: part A and part B spell four authorities differently — "
        "'קריית שמונה'/'קרית שמונה', 'טובא-זנגרייה'/'טובא-זנגריה', 'גולן'/'הגולן', "
        "\"ג'ש (גוש חלב)\"/\"ג'ש )גוש חלב(\". One page, one authority, two names. "
        "CLAUDE.md's approved fix is a 'שם בביטוח לאומי' column in eshkol_mapping.xlsx; "
        "delete this marker once both parts render from it."
    ),
)
def test_should_print_one_name_per_authority_across_the_whole_page(data, btl):
    # Arrange
    part_a = {item["name"] for item in data["authorities"]["items"]}
    part_b = {auth["name"] for auth in btl["authorities"]}

    # Act / Assert
    assert part_a == part_b, (
        f"only in part A: {sorted(part_a - part_b)} · only in part B: {sorted(part_b - part_a)}"
    )


def test_should_pin_the_four_authorities_that_are_spelled_two_ways(data, btl):
    """Pins the defect above so it cannot grow while the marker is in place."""
    # Arrange
    part_a = {item["name"] for item in data["authorities"]["items"]}
    part_b = {auth["name"] for auth in btl["authorities"]}

    # Act
    divergent = (part_a - part_b) | (part_b - part_a)

    # Assert
    assert len(divergent) == 8, (
        f"the number of divergent spellings changed (4 authorities, 8 names): "
        f"{sorted(divergent)}"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN DEFECT, and the fix belongs upstream: the mirrored parentheses in "
        "\"ג'ש )גוש חלב(\" originate in eshkol_mapping.xlsx, column 'שם רשמי בלמס'. "
        "btl.json labels its authorities from that column and carries the artefact "
        "through to the unit selector. The National Insurance tables themselves "
        "spell it \"ג'ש (גוש חלב)\" correctly, so nothing downstream introduced it — "
        "correct the mapping workbook, not the pipeline."
    ),
)
def test_should_never_publish_an_authority_name_with_mirrored_brackets(data, btl):
    # Arrange
    names = [item["name"] for item in data["authorities"]["items"]]
    names += [auth["name"] for auth in btl["authorities"]]

    # Act
    malformed = [
        name
        for name in names
        if name.count("(") != name.count(")")
        or ("(" in name and ")" in name and name.index(")") < name.index("("))
    ]

    # Assert
    assert malformed == [], f"authority names with broken brackets: {malformed}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "PENDING ACTION recorded in CLAUDE.md (30/08/2026): add a 'שם בביטוח לאומי' "
        "column to eshkol_mapping.xlsx so the National Insurance spellings resolve "
        "exactly, 'ולא להסתמך על fuzzy בזמן ריצה'. Until then two of the eighteen "
        "authorities match only through difflib at runtime."
    ),
)
def test_should_carry_the_national_insurance_spelling_in_the_mapping():
    # Arrange
    frame = pd.read_excel(paths.ESHKOL_MAPPING_XLSX)

    # Act / Assert
    assert "שם בביטוח לאומי" in frame.columns, (
        f"the mapping still has only {list(frame.columns)}"
    )


def test_should_pin_how_many_authorities_still_rely_on_fuzzy_matching(matcher, data):
    """Names that need difflib are the ones the pending column would make exact."""
    # Arrange
    names = [item["name"] for item in data["authorities"]["items"]]
    east = matcher.target_codes(eshkol_lib.AUTHORITY, eshkol_lib.EAST_GALILEE)
    resolved = _resolved_codes(matcher, names)

    # Act
    fuzzy = [
        name
        for name, code in resolved.items()
        if code in east and matcher._name_matches_code(name, code)[1].startswith("fuzzy")
    ]

    # Assert
    assert len(fuzzy) == 2, (
        f"the number of authorities matched only by similarity changed: {sorted(fuzzy)}"
    )
