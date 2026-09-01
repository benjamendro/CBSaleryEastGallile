"""Unit tests for eshkol_matcher.py — the join every dataset passes through.

The matcher decides which rows of an external table belong to a cluster
authority. Its own SKILL.md calls the cross-check of code AND name mandatory,
because CBS regional-council codes collide with locality codes: code 26 is the
locality ראש פינה and also the regional council מטה יהודה. A matcher that trusts
a code alone silently attributes one authority's data to another.

These are the only tests in the suite that call a unit directly rather than
checking a published artefact, so they exercise the rules the skill states.
"""

import pytest

from _lib import eshkol as eshkol_lib


# --- sanitize: the normalisation every comparison goes through ----------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ('ג\'ש (גוש חלב)', "גש גוש חלב"),        # geresh dropped, brackets keep content
        ("מעלות-תרשיחא", "מעלות תרשיחא"),          # hyphen becomes a space
        ("  צפת  ", "צפת"),                        # outer whitespace trimmed
        ("קריית    שמונה", "קריית שמונה"),          # runs of whitespace collapse
        ('פקיעין (בוקייעה)', "פקיעין בוקייעה"),
        (None, ""),                                # missing name is not an error
    ],
)
def test_should_normalise_a_name_the_same_way_on_both_sides(matcher_module, raw, expected):
    # Arrange / Act
    result = matcher_module.sanitize(raw)

    # Assert
    assert result == expected


def test_should_keep_the_text_inside_brackets_rather_than_dropping_it(matcher_module):
    """Dropping bracketed text would collapse 'ג'ש (גוש חלב)' to 'גש' and mismatch."""
    # Arrange / Act
    result = matcher_module.sanitize("ג'ש (גוש חלב)")

    # Assert
    assert "גוש חלב" in result, f"bracketed text was discarded: {result!r}"


# --- the fuzzy cut-off the skill fixes at 0.85 --------------------------------

def test_should_hold_the_fuzzy_cut_off_at_the_documented_threshold(matcher_module):
    # Arrange / Act / Assert
    assert matcher_module.FUZZY_CUTOFF >= 0.85, (
        f"the fuzzy cut-off is {matcher_module.FUZZY_CUTOFF}; SKILL.md §2.4 sets a "
        "floor of 0.85 and calls anything looser a guess"
    )


def test_should_accept_the_spelling_variants_the_sources_actually_use(matcher):
    """Both spellings of the same authority must resolve to the same code."""
    # Arrange
    variants = [
        ("הגליל העליון", 5501),   # official spelling, also the one the tables use
        ("גליל עליון", 5501),     # the cluster list's spelling
        ("מעלות-תרשיחא", 1063),
        ("פקיעין (בוקייעה)", 536),
    ]

    # Act / Assert
    for name, code in variants:
        ok, how = matcher._name_matches_code(name, code)
        assert ok, f"{name!r} was not accepted for code {code} ({how})"


def test_should_reject_a_name_that_is_merely_similar(matcher):
    # Arrange / Act
    ok, how = matcher._name_matches_code("תל אביב", 5501)

    # Assert
    assert not ok, f"'תל אביב' was accepted for the Upper Galilee council ({how})"
    assert how == "name_mismatch"


def test_should_reject_an_empty_name_rather_than_matching_on_the_code(matcher):
    # Arrange / Act
    ok, how = matcher._name_matches_code("", 5501)

    # Assert
    assert not ok and how == "empty_name", f"an empty name resolved to a target ({how})"


# --- the double key: the collision the skill was written for ------------------

def test_should_reject_a_row_whose_code_and_name_disagree(matcher):
    """Code 26 is ראש פינה in this mapping; a row calling it מטה יהודה is the collision."""
    import pandas as pd

    # Arrange
    frame = pd.DataFrame([{"name": "מטה יהודה", "code": 26}])

    # Act
    result, errors = matcher.match_dataframe(frame, name_col="name", code_col="code")

    # Assert
    assert not result["matched"].iloc[0], "a colliding code was accepted as a match"
    assert result["match_status"].iloc[0] == "code_name_mismatch"
    assert [error["issue"] for error in errors] == ["code_name_mismatch"], (
        f"the collision was not reported as a hard error: {errors}"
    )


def test_should_match_a_row_whose_code_and_name_agree(matcher):
    import pandas as pd

    # Arrange
    frame = pd.DataFrame([{"name": "ראש פינה", "code": 26}])

    # Act
    result, errors = matcher.match_dataframe(frame, name_col="name", code_col="code")

    # Assert
    assert result["matched"].iloc[0], f"a valid row was rejected: {result.iloc[0].to_dict()}"
    assert result["match_code"].iloc[0] == 26
    assert errors == [], f"a clean row produced errors: {errors}"


def test_should_leave_a_code_outside_the_cluster_unmatched_without_erroring(matcher):
    """An out-of-scope authority is not a data fault — it is simply not ours."""
    import pandas as pd

    # Arrange
    frame = pd.DataFrame([{"name": "תל אביב-יפו", "code": 5000}])

    # Act
    result, errors = matcher.match_dataframe(frame, name_col="name", code_col="code")

    # Assert
    assert not result["matched"].iloc[0]
    assert result["match_status"].iloc[0] == "out_of_scope"
    assert errors == [], f"an out-of-scope row was reported as an error: {errors}"


def test_should_warn_when_a_match_rests_on_the_name_alone(matcher):
    """National Insurance tables carry no CBS codes, so this path is the real one."""
    import pandas as pd

    # Arrange
    frame = pd.DataFrame([{"name": "קריית שמונה"}])

    # Act
    result, errors = matcher.match_dataframe(frame, name_col="name")

    # Assert
    assert result["matched"].iloc[0], "a known authority failed to match by name"
    assert result["match_status"].iloc[0] == "name_only"
    assert [error["issue"] for error in errors] == ["name_only_no_code"], (
        "matching without a code to cross-check must be reported, per SKILL.md §3"
    )


# --- reporting what is absent -------------------------------------------------

def test_should_report_the_cluster_authorities_a_dataset_never_mentions(matcher):
    # Arrange
    east_codes = matcher.target_codes(eshkol_lib.AUTHORITY, eshkol_lib.EAST_GALILEE)
    found = east_codes[:-1]

    # Act
    missing = matcher.verify_targets_present(
        found, entity_type=eshkol_lib.AUTHORITY, affiliation=eshkol_lib.EAST_GALILEE
    )

    # Assert
    assert [item["code"] for item in missing] == [east_codes[-1]], (
        f"the absent authority was not reported: {missing}"
    )


def test_should_report_nothing_missing_when_every_authority_is_present(matcher):
    # Arrange
    east_codes = matcher.target_codes(eshkol_lib.AUTHORITY, eshkol_lib.EAST_GALILEE)

    # Act
    missing = matcher.verify_targets_present(
        east_codes, entity_type=eshkol_lib.AUTHORITY, affiliation=eshkol_lib.EAST_GALILEE
    )

    # Assert
    assert missing == [], f"authorities reported missing although all were supplied: {missing}"
