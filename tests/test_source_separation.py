"""The rule the whole dashboard is built around.

CLAUDE.md, in bold: a National Insurance wage in shekels may never be placed
beside a CBS wage in shekels — not on one axis, not in one chart, not on one
metric card; no percentage change may take its base from one source and its
target from the other; and the two series may never be chained.

The two sources measure the same people and disagree on wage level by 8.7%–27.2%,
so a figure that crosses the line is wrong in a way no reader can detect. These
tests check the separation where it is machine-checkable: inside the data, and in
the structure of the page.
"""

import re

CBS_NATIONAL_SALARY = 12_975.83


def test_should_attribute_each_part_to_a_different_source(data, btl):
    # Arrange
    part_a = data["meta"]["source"]
    part_b = btl["meta"]["source"]

    # Act / Assert
    assert "סטטיסטיקה" in part_a, f"part A no longer names the CBS as its source: {part_a!r}"
    assert "ביטוח לאומי" in part_b, (
        f"part B no longer names National Insurance as its source: {part_b!r}"
    )
    assert part_a != part_b, "both parts now claim the same source"


def test_should_warn_that_the_two_parts_cannot_be_compared(btl):
    """The page must say so itself, not only the repository's documentation."""
    # Arrange
    note = btl["meta"]["note"]

    # Act / Assert
    assert "אינם ניתנים להשוואה" in note, (
        f"part B no longer warns against comparing it with part A: {note!r}"
    )
    assert re.search(r"8\.7%[^\d]{0,3}27\.2%", note), (
        "the warning no longer states the measured size of the gap"
    )


def test_should_compute_the_national_ratio_inside_a_single_source(data):
    """data.btl is National Insurance; its ratio must divide BTL by BTL."""
    # Arrange
    rows = data["btl"]["rows"]

    # Act
    wrong = [
        (row["year"], row["ratio"], round(row["salary"] / row["national"], 4))
        for row in rows
        if abs(row["ratio"] - round(row["salary"] / row["national"], 4)) > 1e-4
    ]

    # Assert
    assert wrong == [], f"the trend ratio is not salary ÷ national within one source: {wrong}"


def test_should_never_divide_the_national_insurance_series_by_the_cbs_average(data):
    """The clearest way the rule could break: a ratio taken against 12,975.83."""
    # Arrange
    rows = data["btl"]["rows"]

    # Act
    crossed = [
        row["year"]
        for row in rows
        if abs(row["ratio"] - row["salary"] / CBS_NATIONAL_SALARY) < 1e-4
    ]

    # Assert
    assert crossed == [], (
        f"the trend ratio for {crossed} equals salary ÷ the CBS national average — "
        "that is a cross-source ratio, which CLAUDE.md forbids"
    )


def test_should_keep_the_national_insurance_national_series_off_the_cbs_figure(data):
    """The two sources' national wages are different numbers and must stay so."""
    # Arrange
    nationals = {row["year"]: row["national"] for row in data["btl"]["rows"]}

    # Act
    identical = [year for year, value in nationals.items() if value == CBS_NATIONAL_SALARY]

    # Assert
    assert identical == [], (
        f"the National Insurance national wage for {identical} is exactly the CBS "
        f"figure {CBS_NATIONAL_SALARY} — one has been copied into the other"
    )


def test_should_stop_the_cbs_trend_before_the_national_insurance_years_begin(data, btl):
    """Chaining the two series is forbidden; the CBS part covers one year only."""
    # Arrange
    cbs_year = int(data["meta"]["year"])
    btl_trend_years = {int(row["year"]) for row in data["btl"]["rows"]}

    # Act / Assert
    assert cbs_year not in btl_trend_years, (
        f"the CBS year {cbs_year} also appears in the National Insurance trend — "
        "the two series are being chained"
    )
    assert max(btl_trend_years) < cbs_year, (
        "the National Insurance trend now reaches the CBS year; verify no reader can "
        "read the two as one continuous line"
    )


def test_should_separate_the_two_parts_with_a_declared_break_in_the_page(template_html):
    """CLAUDE.md · 'מפריד מקורות' — the switch of source has to be visible."""
    # Arrange / Act / Assert
    assert 'id="srcbreak"' in template_html, (
        "the source divider element is gone; part B would follow part A with nothing "
        "telling the reader the source changed"
    )
    assert "מפריד מקורות" in template_html, (
        "the divider is no longer labelled as a source break in the page source"
    )


def test_should_carry_one_context_bar_per_part(template_html):
    """'הקשר אחד בכל רגע' — the metric bar and the population bar must be separate
    elements the page can hide independently, not one shared bar."""
    # Arrange / Act
    has_metric_bar = "metricbar" in template_html
    has_context_bar = 'id="ctxbar"' in template_html
    can_hide = re.search(r"\.metricbar\.off\s*,\s*\.ctxbar\.off", template_html)

    # Assert
    assert has_metric_bar and has_context_bar, (
        "the page no longer has one bar per part (metricbar for A, ctxbar for B)"
    )
    assert can_hide, (
        "neither bar can be switched off; the two contexts could be shown together"
    )


def test_should_state_the_wage_gap_where_the_reader_meets_both_parts(template_html):
    # Arrange / Act / Assert
    assert re.search(r"8\.7%\s*[–-]\s*27\.2%", template_html), (
        "the page no longer tells the reader how far apart the two sources' wage "
        "levels are, so nothing warns against comparing them"
    )
