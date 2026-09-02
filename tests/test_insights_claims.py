"""Are the insights grounded in the data they cite?

analysis/dashboard-insights.md is a qualitative document: fourteen insights, each
stating figures and drawing a conclusion from them. These tests take every headline
figure back to the table it claims to come from, and — where a conclusion depends
on more than arithmetic — check that the conclusion actually follows.

Two things are checked separately and must not be confused:
  * the figures reproduce (an arithmetic question), and
  * the claim built on them holds (an inferential one).
A number can be right and the sentence around it still wrong.
"""

import numpy as np
import pytest

from _lib import analysis

TOL = 0.06  # the document rounds to one decimal place


def _close(actual, expected, tol=TOL):
    return abs(actual - expected) <= tol


# --- insight 1 · the relative gap is frozen, the shekel gap widens ------------

@pytest.fixture(scope="module")
def wage_year():
    return analysis.table("wage_wage_year_mean.csv")


def test_insight_1_should_quote_the_wage_levels_the_series_holds(wage_year):
    # Arrange
    expected = {2016: (7565, 9573, 11157), 2022: (9096, 11657, 14481), 2024: (10266, 12844, 15937)}

    # Act / Assert
    for year, (cluster, national, tel_aviv) in expected.items():
        row = wage_year.loc[year]
        assert round(row["אשכול גליל מזרחי"]) == cluster, f"{year} cluster wage"
        assert round(row["ארצי"]) == national, f"{year} national wage"
        assert round(row["תל־אביב"]) == tel_aviv, f"{year} Tel Aviv wage"


def test_insight_1_should_show_a_flat_ratio_beside_a_widening_shekel_gap(wage_year):
    """The whole insight rests on these two series moving differently."""
    # Arrange
    gap = wage_year["ארצי"] - wage_year["אשכול גליל מזרחי"]
    share = 100 * gap / wage_year["ארצי"]

    # Act / Assert
    assert round(gap.loc[2016]) == 2008 and round(gap.loc[2024]) == 2578
    assert share.max() - share.min() < 2.0, (
        f"the relative gap is no longer flat: {share.min():.1f}–{share.max():.1f}%"
    )
    assert gap.loc[2024] > gap.loc[2016] * 1.2, "the shekel gap is no longer widening"


def test_insight_1_should_report_the_tel_aviv_gap_growth_it_claims(wage_year):
    # Arrange / Act
    first = wage_year.loc[2016, "תל־אביב"] - wage_year.loc[2016, "אשכול גליל מזרחי"]
    last = wage_year.loc[2024, "תל־אביב"] - wage_year.loc[2024, "אשכול גליל מזרחי"]

    # Assert
    assert round(first) == 3592 and round(last) == 5671
    assert round(last - first) == 2079, "the quoted 2,079 ₪ increase no longer holds"


# --- insight 2 · the two ends of the distribution -----------------------------

@pytest.fixture(scope="module")
def peers():
    return analysis.table("dist_vs_peers.csv", index_col=None)


def test_insight_2_should_find_a_real_excess_at_the_bottom_of_the_distribution(peers):
    from scipy import stats

    # Arrange / Act
    mean = peers["d_minw"].mean()
    positive = int((peers["d_minw"] > 0).sum())
    p_value = stats.ttest_1samp(peers["d_minw"], 0).pvalue

    # Assert
    assert _close(mean, 1.9, 0.05), f"the bottom-end excess is {mean:+.2f}, not +1.9"
    assert positive == 13, f"{positive} of 17 authorities are above their peers, not 13"
    assert _close(p_value, 0.014, 0.001), f"p = {p_value:.4f}, not 0.014"


def test_insight_2_should_find_nothing_at_the_top_of_the_distribution(peers):
    from scipy import stats

    # Arrange / Act
    mean = peers["d_top"].mean()
    p_value = stats.ttest_1samp(peers["d_top"], 0).pvalue

    # Assert
    assert _close(mean, 0.12, 0.01), f"the top-end difference is {mean:+.3f}, not +0.12"
    assert p_value > 0.3, (
        f"the top-end difference is now significant (p={p_value:.3f}); the insight's "
        "claim that it is 'the same fact said twice' would need revisiting"
    )


def test_insight_2_should_compare_each_authority_against_a_usable_peer_group(peers):
    """A claim about 'similar authorities' is only as good as the groups behind it."""
    # Arrange / Act / Assert
    assert peers["peers"].min() >= 12, f"an authority has only {peers['peers'].min()} peers"
    assert peers["peers"].max() <= 35, "a peer group grew beyond the documented 35"
    assert len(peers) == 17, f"{len(peers)} authorities compared, not 17"


def test_insight_2_should_place_the_excess_where_the_insight_says_it_is(peers):
    # Arrange
    named = {"מג'דל שמס", "בוקעתא", "מסעדה", "מטולה", "ראש פינה", "צפת"}

    # Act
    top_six = set(peers.nlargest(6, "d_minw")["name"])

    # Assert
    assert top_six == named, f"the six most excessive are now {sorted(top_six)}"
    below = set(peers.nsmallest(2, "d_minw")["name"])
    assert below == {"חצור הגלילית", "טובא-זנגריה"}, (
        f"the two authorities below their peers are now {sorted(below)}"
    )


# --- insight 3 · the internal ranking is frozen -------------------------------

def test_insight_3_should_rest_on_a_rank_correlation_that_is_actually_high():
    """Reported as Spearman 0.979; the claim 'nothing moved' needs it near 1."""
    # Arrange
    text = analysis.insight(3)

    # Act / Assert
    assert "0.979" in text, "the reported rank correlation changed"
    assert "p=0.20" in text or "p=0.199" in text or "0.20" in text, (
        "the convergence test's p-value is no longer stated"
    )


# --- insight 4 · the 2024 shock is a border story -----------------------------

@pytest.fixture(scope="module")
def profile():
    return analysis.table("authority_profile.csv")


def test_insight_4_should_separate_the_border_authorities_from_the_rest(profile):
    # Arrange
    border = ["עג'ר", "קרית שמונה", "מטולה", "גליל עליון", "מבואות חרמון"]
    assert set(border) <= set(profile.index), "the border authorities are not all present"

    # Act
    def group(names):
        now = profile.loc[names, "מועסקים"]
        before = now / (1 + profile.loc[names, "שינוי_מועסקים_23_24"] / 100)
        return now.sum(), before.sum()

    border_now, border_before = group(border)
    rest = [name for name in profile.index if name not in border]
    rest_now, rest_before = group(rest)

    # Assert
    assert round(border_now) == 28224, f"border employment is {border_now:,.0f}"
    assert _close(100 * (border_now / border_before - 1), -10.3, 0.1)
    assert round(rest_now) == 64195, f"the rest employ {rest_now:,.0f}"
    assert _close(100 * (rest_now / rest_before - 1), -0.9, 0.1)


def test_insight_4_should_hold_that_the_shock_is_not_cluster_wide(profile):
    """The claim is comparative: the border fell an order of magnitude harder."""
    # Arrange
    border = ["עג'ר", "קרית שמונה", "מטולה", "גליל עליון", "מבואות חרמון"]
    rest = [name for name in profile.index if name not in border]

    # Act
    border_drop = profile.loc[border, "שינוי_מועסקים_23_24"].mean()
    grew = int((profile.loc[rest, "שינוי_מועסקים_23_24"] > 0).sum())

    # Assert
    assert border_drop < -5, f"the border authorities' mean change is {border_drop:+.1f}%"
    assert grew >= 3, f"only {grew} of the other authorities grew; the insight says three"


# --- insight 5 · the 2024 'improvement' is composition ------------------------

def test_insight_5_should_lose_its_employment_from_the_bottom_of_the_distribution(profile):
    """The claim: 95% of the people lost earned below the national average."""
    # Arrange
    now = profile["מועסקים"]
    before = now / (1 + profile["שינוי_מועסקים_23_24"] / 100)

    # Act
    lost = before.sum() - now.sum()

    # Assert
    assert round(lost) == 3816, f"the cluster lost {lost:,.0f}, not 3,816"
    assert _close(100 * (now.sum() / before.sum() - 1), -4.0, 0.05)


def test_insight_5_should_warn_against_reading_2024_as_improvement():
    """The insight's operative instruction — it must survive edits to the prose."""
    # Arrange
    text = analysis.insight(5)

    # Act / Assert
    assert "אפקט הרכב" in text, "the composition-effect explanation is gone"
    assert "אסור להציג" in text and "מספר המועסקים" in text, (
        "the instruction never to show the 2024 wage rise without the headcount is gone"
    )


# --- insight 7 · four knowledge industries ------------------------------------

@pytest.fixture(scope="module")
def shiftshare():
    return analysis.table("shiftshare.csv")


def test_insight_7_should_decompose_the_gap_without_leaving_a_residual(shiftshare):
    """A symmetric decomposition is the reason the 77% figure is trustworthy."""
    # Arrange / Act
    mix = shiftshare["c_mix"].sum()
    pay = shiftshare["c_pay"].sum()
    total = shiftshare["tot"].sum()

    # Assert
    assert _close(mix, -797, 1) and _close(pay, -1772, 1), f"mix {mix:.0f}, pay {pay:.0f}"
    assert _close(mix + pay, total, 0.5), "the two components no longer sum to the gap"
    assert _close(total, -2569, 1), f"the gap is {total:.0f}, not -2,569"


def test_insight_7_should_attribute_77_percent_of_the_net_gap_to_four_industries(shiftshare):
    # Arrange
    knowledge = shiftshare[shiftshare["ענף"].str.contains("תכנות|פיננס|מחקר|אלקטרוני", na=False)]

    # Act
    share_of_net = 100 * knowledge["tot"].sum() / shiftshare["tot"].sum()

    # Assert
    assert len(knowledge) == 4, f"{len(knowledge)} knowledge industries matched, not 4"
    assert _close(knowledge["tot"].sum(), -1982, 1)
    assert _close(share_of_net, 77, 0.5), f"they carry {share_of_net:.0f}% of the net gap"


def test_insight_7_should_state_the_smaller_share_of_the_downward_pull(shiftshare):
    """The insight's own warning: 77% of the *net* gap is 49% of the pull down."""
    # Arrange
    knowledge = shiftshare[shiftshare["ענף"].str.contains("תכנות|פיננס|מחקר|אלקטרוני", na=False)]
    downward = shiftshare[shiftshare["tot"] < 0]

    # Act
    share_of_pull = 100 * knowledge["tot"].sum() / downward["tot"].sum()

    # Assert
    assert len(downward) == 32, f"{len(downward)} industries pull down, not 32"
    assert _close(downward["tot"].sum(), -4070, 2)
    assert _close(share_of_pull, 49, 0.5), f"they are {share_of_pull:.0f}% of the pull down"
    assert "49%" in analysis.insight(7), "the qualifying 49% figure is no longer stated"


# --- insight 8 · the big local industries pay like the country ----------------

def test_insight_8_should_show_the_cluster_paying_near_the_national_rate(shiftshare):
    # Arrange
    expected = {"חינוך": 103, "ייצור מוצרי מזון": 101, "גידולים צמחיים": 97}

    # Act / Assert
    for name, ratio in expected.items():
        row = shiftshare[shiftshare["ענף"] == name]
        assert len(row) == 1, f"{name} matched {len(row)} rows"
        assert _close(row["w_ratio"].iloc[0], ratio, 0.6), (
            f"{name} pays {row['w_ratio'].iloc[0]:.0f}% of the national rate, not {ratio}%"
        )


def test_insight_8_should_rest_on_industries_that_are_actually_large_locally(shiftshare):
    """'עמוד השדרה של התעסוקה' has to mean a large local share."""
    # Arrange
    education = shiftshare[shiftshare["ענף"] == "חינוך"].iloc[0]
    farming = shiftshare[shiftshare["ענף"] == "גידולים צמחיים"].iloc[0]

    # Act / Assert
    assert education["s_eg"] > education["s_nat"], "education is no longer over-represented"
    assert farming["s_eg"] / farming["s_nat"] > 4, (
        "farming is no longer employed several times its national weight"
    )


# --- insight 9 · self-employment income varies less ---------------------------

@pytest.fixture(scope="module")
def self_vs_employee():
    return analysis.table("self_vs_employee.csv")


def test_insight_9_should_show_the_narrower_spread_it_claims(self_vs_employee):
    # Arrange
    employees = self_vs_employee["emp_y"]
    self_employed = self_vs_employee["self_y"]

    # Act / Assert
    assert _close(employees.max() / employees.min(), 1.91, 0.01)
    assert _close(self_employed.max() / self_employed.min(), 1.47, 0.01)
    assert _close(100 * employees.std() / employees.mean(), 21.8, 0.1)
    assert _close(100 * self_employed.std() / self_employed.mean(), 11.3, 0.1)


def test_insight_9_should_report_a_variance_ratio_that_the_tests_support(self_vs_employee):
    from scipy import stats

    # Arrange
    log_emp = np.log(self_vs_employee["emp_y"])
    log_self = np.log(self_vs_employee["self_y"])

    # Act
    ratio = log_emp.var(ddof=1) / log_self.var(ddof=1)
    levene = stats.levene(log_emp, log_self, center="mean").pvalue
    brown = stats.levene(log_emp, log_self, center="median").pvalue

    # Assert
    assert _close(ratio, 3.66, 0.02), f"the variance ratio is {ratio:.2f}, not 3.66"
    assert _close(levene, 0.005, 0.001), f"Levene p = {levene:.4f}"
    assert _close(brown, 0.009, 0.001), f"Brown-Forsythe p = {brown:.4f}"


def test_insight_9_should_keep_the_retraction_of_its_earlier_wider_claim():
    """The insight documents a circular correlation it withdrew. That must stay."""
    # Arrange
    text = analysis.insight(9)

    # Act / Assert
    assert "מעגלי" in text, "the note that the earlier −0.84 correlation was circular is gone"
    assert "מה לא ניתן לומר" in text, "the limits section is gone"


# --- insight 11 · where residents earn the national rate ----------------------

@pytest.fixture(scope="module")
def industry_ratio():
    return analysis.table("anaf_authority_ratio.csv", index_col=None)


def test_insight_11_should_count_the_cells_at_or_above_the_national_rate(industry_ratio):
    # Arrange / Act
    total = len(industry_ratio)
    at_or_above = int((industry_ratio["ratio"] >= 100).sum())

    # Assert
    assert total == 369, f"{total} industry×authority cells, not 369"
    assert at_or_above == 104, f"{at_or_above} cells at or above the national rate, not 104"
    assert _close(100 * at_or_above / total, 28, 0.5)


def test_insight_11_should_honour_its_own_minimum_base(industry_ratio):
    # Arrange / Act / Assert
    assert industry_ratio["n"].min() >= 50, (
        f"a published cell has only {industry_ratio['n'].min()} employees, below the stated 50"
    )


def test_insight_11_should_contrast_the_two_authorities_it_names(industry_ratio):
    # Arrange
    grouped = industry_ratio.groupby("rashut")

    # Act
    upper = grouped.get_group("הגליל העליון")
    safed = grouped.get_group("צפת")

    # Assert
    assert len(upper) == 36 and int((upper["ratio"] >= 100).sum()) == 25
    assert _close(upper["ratio"].median(), 112, 0.5)
    assert len(safed) == 37 and int((safed["ratio"] >= 100).sum()) == 1
    assert _close(safed["ratio"].median(), 73, 0.5)


# --- insight 12 · which of the two causes is at work --------------------------

@pytest.fixture(scope="module")
def authority_shiftshare():
    return analysis.table("anaf_shiftshare_authority.csv")


def test_insight_12_should_attribute_most_of_each_gap_to_pay_within_industry(
    authority_shiftshare
):
    # Arrange
    negative = authority_shiftshare[authority_shiftshare["פער"] < 0]

    # Act
    # the document states these rounded to whole percent, so compare them that way
    pay_share = (100 * negative["שכר_בתוך_ענף"] / negative["פער"]).round(0)

    # Assert
    within_range = pay_share[(pay_share >= 66) & (pay_share <= 83)]
    assert len(within_range) == 7, (
        f"{len(within_range)} authorities fall in the stated 66–83% band, not 7: "
        f"{pay_share.round(0).to_dict()}"
    )


def test_insight_12_should_single_out_the_two_authorities_that_break_the_pattern(
    authority_shiftshare
):
    # Arrange / Act
    golan = authority_shiftshare.loc["גולן"]
    upper = authority_shiftshare.loc["גליל עליון"]

    # Assert
    assert golan["שכר_בתוך_ענף"] > 0, "the Golan's pay component is no longer positive"
    assert golan["פער"] < 0, "the Golan no longer has a gap to explain"
    assert upper["פער"] > 0, "the Upper Galilee no longer earns above the adjusted standard"
    assert _close(upper["פער"], 341, 1)


def test_insight_12_should_restrict_itself_to_well_covered_authorities(
    authority_shiftshare
):
    """The stated guard against bias from suppressed cells."""
    # Arrange / Act / Assert
    assert len(authority_shiftshare) == 9, f"{len(authority_shiftshare)} authorities included"
    assert authority_shiftshare["כיסוי"].min() >= 80, (
        f"an authority with {authority_shiftshare['כיסוי'].min()}% coverage was included"
    )


# --- insight 13 · how much of the gap is the cluster's own --------------------

@pytest.fixture(scope="module")
def districts():
    return analysis.table("anaf22_districts.csv")


def test_insight_13_should_place_the_cluster_lowest_in_the_country(districts):
    # Arrange / Act
    lowest = districts["שכר"].idxmin()

    # Assert
    assert lowest == "נפות צפת וגולן", f"the lowest-paying region is now {lowest}"


def test_insight_13_should_split_the_gap_ninety_ten(districts):
    # Arrange
    national = analysis.weighted(districts["שכר"], districts["שכירים"])
    north = districts.loc["מחוז צפון ללא", "שכר"]
    cluster = districts.loc["נפות צפת וגולן", "שכר"]

    # Act
    regional = national - north
    own = north - cluster

    # Assert
    assert _close(national, 11986, 1), f"the national mean is {national:.0f}"
    assert _close(100 * regional / (regional + own), 90, 1), (
        f"the regional step is {100 * regional / (regional + own):.0f}% of the gap"
    )
    assert _close(own, 255, 1), f"the cluster's own step is {own:.0f} ₪"


def test_insight_13_should_keep_the_framing_warning_it_carries():
    # Arrange / Act / Assert
    assert "פתרון אשכולי לבדו" in analysis.insight(13), (
        "the warning that a cluster-only remedy closes at most a tenth of the gap is gone"
    )


# --- insight 14 · what happened to the industries 2022 → 2024 -----------------

@pytest.fixture(scope="module")
def industry_change():
    return analysis.table("anaf22_industry_change.csv")


def test_insight_14_should_show_the_cluster_lagging_the_country(industry_change):
    # Arrange / Act
    cluster = 100 * (industry_change["n24"].sum() / industry_change["n22"].sum() - 1)
    national = 100 * (industry_change["N24"].sum() / industry_change["N22"].sum() - 1)

    # Assert
    assert _close(cluster, -0.5, 0.1), f"the cluster changed {cluster:+.1f}%"
    assert _close(national, 3.5, 0.1), f"the country changed {national:+.1f}%"


def test_insight_14_should_rank_the_leisure_industries_as_the_worst_hit(industry_change):
    """The insight names four; they must still be the four largest excess falls."""
    # Arrange
    large = industry_change[industry_change["n22"] >= 400].copy()
    large["excess"] = large["dn"] - large["dn_nat"]

    # Act
    worst = list(large.nsmallest(4, "excess").index.astype(str))

    # Assert
    assert worst == ["93", "55", "90+91+92", "45"], (
        f"the four hardest-hit industries are now {worst}"
    )


def test_insight_14_should_warn_that_a_shrinking_industry_looks_like_a_raise(
    industry_change
):
    """Every industry that shrank shows a better wage ratio — the same composition trap."""
    # Arrange
    large = industry_change[industry_change["n22"] >= 400].copy()
    large["excess"] = large["dn"] - large["dn_nat"]
    worst = large.nsmallest(4, "excess")

    # Act
    improved = int((worst["ratio24"] > worst["ratio22"]).sum())

    # Assert
    assert improved >= 3, (
        "the shrinking industries no longer show improving wage ratios; the insight's "
        "methodological warning may no longer apply"
    )
    assert "אין להציג" in analysis.insight(14), "the warning against pairing the two is gone"


# --- a base mismatch that runs through several insights -----------------------

def test_should_aggregate_the_authority_shares_to_the_cluster_share(profile):
    """The same quantity has two values in two outputs, and the document uses both.

    income_dist.csv reports the cluster at 35.0% earning up to minimum wage in 2024.
    authority_profile.csv's per-authority column, weighted by employment, gives
    38.3%. They differ because the profile takes aggfunc='mean' over *both*
    income-group tables — 'ממוצע לחודש בשנה' and 'ממוצע לחודש עבודה', whose national
    values are 35.5% and 29.9% — while income_dist filters to the second alone.
    Insight 2 quotes 35.0%; insights 5 and 6 build on the blended per-authority
    figures and compare them to that same 29.9% national reference.
    """
    # Arrange
    employees = profile["מועסקים"]
    income = analysis.table("income_dist.csv")

    # Act
    aggregated = analysis.weighted(profile["עד_שכר_מינימום"], employees)
    published = income.loc[income.index[0], "אשכול 2024"]

    # Assert — the gap is the finding; this pins its size
    assert abs(aggregated - published) > 3, (
        "the two outputs now agree on the cluster's minimum-wage share; if the "
        "profile was rebuilt on one measure, the insights that compare it to the "
        "29.9% national figure can be stated consistently and this test removed"
    )
    assert _close(aggregated, 38.35, 0.1), (
        f"the blended aggregate moved to {aggregated:.2f}"
    )
    assert _close(published, 35.0, 0.1), f"income_dist now reports {published}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN ERROR in insight 6ג: 'גליל עליון היא היחידה באשכול שמנצחת את הארצי "
        "בשני הקצוות גם יחד'. On the per-work-month measure — the basis of the 29.9% "
        "and 11.4% national figures the insight itself quotes — גולן beats the "
        "national on both ends too (28.4% up to minimum wage against 29.9%, and 11.5% "
        "above twice the average against 11.4%). The uniqueness claim survives only "
        "because the insight compares blended authority values against single-measure "
        "national ones. Restate it as 'the clearest of two', or put both sides on one "
        "measure and say so."
    ),
)
def test_insight_6c_should_name_the_only_authority_that_beats_both_national_ends():
    # Arrange — on the measure the insight's own national figures come from
    master = analysis.load_master()
    if master is None:
        pytest.skip(
            "the ETL master table is not built; run analysis/etl/parse_btl.py and "
            "build_master.py to check this claim on a single measure"
        )
    table, country = analysis.income_shares(master, "לחודש עבודה")

    # Act
    winners = table[
        (table["inc_minwage"] < country["minimum"]) & (table["top"] > country["top"])
    ]

    # Assert
    assert set(winners.index) == {"הגליל העליון"}, (
        f"authorities beating the national on both ends: {sorted(winners.index)}"
    )


def test_insight_13_should_not_rest_its_2022_claim_on_the_2024_anchor():
    """The insight's stated proof names a figure from a different year.

    It says the 2022 'נפות צפת וגולן' column is exactly the cluster because the 18
    authorities sum to it — citing 83,774, which is the 2024 anchor. In the 2022
    workbook the authorities sum to 84,536 against a column of 83,816: close, but
    not the exact match the sentence claims. The conclusion still holds; the proof
    given for it does not.
    """
    # Arrange
    text = analysis.insight(13)

    # Act / Assert
    assert "83,774" in text, "the anchor figure is no longer quoted"
    assert "במדויק" in text, "the exactness claim is no longer made"
    districts = analysis.table("anaf22_districts.csv")
    cluster_2022 = districts.loc["נפות צפת וגולן", "שכירים"]
    assert cluster_2022 != 83774, (
        f"the 2022 cluster column is {cluster_2022:,.0f}; the insight cites the 2024 "
        "figure 83,774 as its proof, so the two are not the same measurement"
    )


def test_insight_11_should_account_for_every_cell_in_its_own_table(industry_ratio):
    """The table is presented as the picture for all 369 cells; it shows 366."""
    # Arrange
    # the document uses a maqaf where the table uses a hyphen, so compare loosely
    normalise = lambda name: name.replace("־", "-").replace("\u05be", "-")
    text = normalise(analysis.insight(11))
    listed = {
        name for name in industry_ratio["rashut"].unique() if normalise(name) in text
    }

    # Act
    shown = int(industry_ratio[industry_ratio["rashut"].isin(listed)].shape[0])
    missing = sorted(set(industry_ratio["rashut"]) - listed)

    # Assert
    assert shown == 366 and missing == ["יסוד המעלה"], (
        f"the per-authority table now covers {shown} of {len(industry_ratio)} cells; "
        f"absent: {missing}"
    )
