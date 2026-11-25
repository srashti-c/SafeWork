import inspect

import pytest

from app.services import risk_config as cfg
from app.services.risk import calculate_risk, level_for_score


def pts(result, factor):
    for r in result["reasons"]:
        if r["factor"] == factor:
            return r["points"]
    raise AssertionError("factor missing: " + factor)


# ---------- config ----------
def test_weights_add_up_to_100():
    assert sum(cfg.MAX_POINTS.values()) == 100


def test_configured_points_never_exceed_the_factor_maximum():
    assert max(cfg.SEVERITY_BY_CATEGORY.values()) <= cfg.MAX_POINTS["severity"]
    assert max(cfg.FREQUENCY_POINTS.values()) <= cfg.MAX_POINTS["frequency"]
    assert max(cfg.POWER_POINTS.values()) <= cfg.MAX_POINTS["power_imbalance"]
    assert cfg.THREAT_POINTS_MANY_MATCHES <= cfg.MAX_POINTS["threat_language"]
    assert cfg.RETALIATION_POINTS <= cfg.MAX_POINTS["retaliation"]
    assert cfg.RECURRENCE_POINTS_MANY <= cfg.MAX_POINTS["recurrence"]
    assert cfg.EVIDENCE_POINTS_MANY <= cfg.MAX_POINTS["evidence"]


# ---------- severity ----------
@pytest.mark.parametrize("name", list(cfg.SEVERITY_BY_CATEGORY))
def test_severity_matches_config_for_every_category(name):
    assert pts(calculate_risk(name), "severity") == cfg.SEVERITY_BY_CATEGORY[name]


def test_physical_and_sexual_score_higher_than_other():
    other = pts(calculate_risk("Other"), "severity")
    assert pts(calculate_risk("Physical harassment"), "severity") > other
    assert pts(calculate_risk("Sexual harassment"), "severity") > other


def test_category_name_ignores_case_and_spaces():
    assert pts(calculate_risk("  sexual HARASSMENT "), "severity") == cfg.SEVERITY_BY_CATEGORY["Sexual harassment"]


@pytest.mark.parametrize("bad", ["Made up category", "", None, 5])
def test_unknown_category_gets_zero_and_says_so(bad):
    result = calculate_risk(bad)
    assert pts(result, "severity") == 0
    reason = [r for r in result["reasons"] if r["factor"] == "severity"][0]["reason"]
    assert "not recognised" in reason


# ---------- frequency / power ----------
@pytest.mark.parametrize("value", list(cfg.FREQUENCY_POINTS))
def test_frequency_points(value):
    assert pts(calculate_risk("Other", frequency=value), "frequency") == cfg.FREQUENCY_POINTS[value]


@pytest.mark.parametrize("value", list(cfg.POWER_POINTS))
def test_power_imbalance_points(value):
    assert pts(calculate_risk("Other", power_imbalance=value), "power_imbalance") == cfg.POWER_POINTS[value]


def test_manager_scores_higher_than_no_imbalance():
    a = pts(calculate_risk("Other", power_imbalance="direct_manager"), "power_imbalance")
    b = pts(calculate_risk("Other", power_imbalance="none"), "power_imbalance")
    assert a > b


# ---------- threat language ----------
def test_no_threat_phrase_gives_zero():
    r = calculate_risk("Other", text="The canteen food was cold and the AC was broken.")
    assert pts(r, "threat_language") == 0


def test_one_threat_phrase():
    r = calculate_risk("Other", text="My manager said he will ruin your career.")
    assert pts(r, "threat_language") == cfg.THREAT_POINTS_ONE_MATCH


def test_two_threat_phrases():
    r = calculate_risk("Other", text="He said I will kill you if you tell anyone.")
    assert pts(r, "threat_language") == cfg.THREAT_POINTS_MANY_MATCHES


def test_same_phrase_twice_counts_once():
    r = calculate_risk("Other", text="kill you. I said kill you again.")
    assert pts(r, "threat_language") == cfg.THREAT_POINTS_ONE_MATCH


def test_threat_matching_ignores_case_and_curly_apostrophe():
    assert pts(calculate_risk("Other", text="I WILL KILL YOU"), "threat_language") == cfg.THREAT_POINTS_ONE_MATCH
    assert pts(calculate_risk("Other", text="you\u2019ll regret this"), "threat_language") == cfg.THREAT_POINTS_ONE_MATCH


def test_threat_reason_names_the_phrase():
    r = calculate_risk("Other", text="He will ruin your career.")
    reason = [x for x in r["reasons"] if x["factor"] == "threat_language"][0]["reason"]
    assert "ruin your career" in reason


@pytest.mark.parametrize("bad", [None, 123, ["kill you"]])
def test_non_text_input_does_not_crash(bad):
    assert pts(calculate_risk("Other", text=bad), "threat_language") == 0


# ---------- retaliation / recurrence / evidence ----------
def test_retaliation_flag_off_by_default():
    assert pts(calculate_risk("Other"), "retaliation") == 0


def test_retaliation_flag_on():
    assert pts(calculate_risk("Other", retaliation_flag=True), "retaliation") == cfg.RETALIATION_POINTS


@pytest.mark.parametrize("count,expected", [
    (0, 0), (1, cfg.RECURRENCE_POINTS_ONE), (2, cfg.RECURRENCE_POINTS_MANY), (9, cfg.RECURRENCE_POINTS_MANY)])
def test_recurrence_points(count, expected):
    assert pts(calculate_risk("Other", recurrence_count=count), "recurrence") == expected


@pytest.mark.parametrize("count,expected", [
    (0, 0), (1, cfg.EVIDENCE_POINTS_ONE), (2, cfg.EVIDENCE_POINTS_MANY), (10, cfg.EVIDENCE_POINTS_MANY)])
def test_evidence_points(count, expected):
    assert pts(calculate_risk("Other", evidence_count=count), "evidence") == expected


# ---------- bad inputs ----------
def test_bad_frequency_and_power_raise():
    with pytest.raises(ValueError):
        calculate_risk("Other", frequency="sometimes")
    with pytest.raises(ValueError):
        calculate_risk("Other", power_imbalance="boss")


@pytest.mark.parametrize("bad", [-1, 1.5, "2", None, True])
def test_bad_counts_raise(bad):
    with pytest.raises(ValueError):
        calculate_risk("Other", recurrence_count=bad)
    with pytest.raises(ValueError):
        calculate_risk("Other", evidence_count=bad)


# ---------- levels ----------
def test_four_levels_and_lowest_cutoff_is_zero():
    assert {n for _, n in cfg.LEVEL_CUTOFFS} == {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert min(cfg.LEVEL_CUTOFFS)[0] == 0


def test_each_cutoff_is_inclusive_and_one_below_is_the_lower_level():
    cuts = sorted(cfg.LEVEL_CUTOFFS)
    for i, (cutoff, name) in enumerate(cuts):
        assert level_for_score(cutoff) == name
        if i > 0:
            assert level_for_score(cutoff - 1) == cuts[i - 1][1]


def test_score_100_is_the_top_level_and_0_is_the_bottom_level():
    assert level_for_score(100) == max(cfg.LEVEL_CUTOFFS)[1]
    assert level_for_score(0) == "LOW"


def test_maximum_case_scores_100_and_top_level():
    r = calculate_risk(
        "Sexual harassment", text="I will kill you if you tell anyone",
        frequency="repeated", power_imbalance="direct_manager",
        retaliation_flag=True, recurrence_count=3, evidence_count=3)
    assert r["score"] == 100
    assert r["max_score"] == 100
    assert r["level"] == max(cfg.LEVEL_CUTOFFS)[1]


def test_minimal_case_level_matches_its_score():
    r = calculate_risk("Other")
    assert r["score"] == cfg.SEVERITY_BY_CATEGORY["Other"]
    assert r["level"] == level_for_score(r["score"])


# ---------- reasons list ----------
def test_reasons_list_has_all_seven_factors_in_order():
    r = calculate_risk("Other")
    assert [x["factor"] for x in r["reasons"]] == list(cfg.MAX_POINTS)


def test_reason_points_add_up_to_the_score():
    r = calculate_risk("Discrimination", text="if you complain", frequency="a_few",
                       power_imbalance="senior", evidence_count=1)
    assert sum(x["points"] for x in r["reasons"]) == r["score"]


def test_every_reason_has_text_and_a_valid_max():
    r = calculate_risk("Other")
    for x in r["reasons"]:
        assert set(x) == {"factor", "points", "max_points", "reason"}
        assert x["reason"].strip() != ""
        assert 0 <= x["points"] <= x["max_points"]


# ---------- notice ----------
def test_notice_says_priority_only_not_probability_of_guilt():
    n = calculate_risk("Other")["notice"]
    assert "PRIORITY ONLY" in n
    assert "NOT a probability of guilt" in n
    assert "human reviewer" in n
    assert "Internal Committee" in n


def test_notice_is_present_for_every_level():
    low = calculate_risk("Other")
    top = calculate_risk("Sexual harassment", text="kill you if you tell",
                         frequency="repeated", power_imbalance="direct_manager",
                         retaliation_flag=True, recurrence_count=2, evidence_count=2)
    assert low["notice"] == cfg.NOTICE and top["notice"] == cfg.NOTICE


# ---------- design rules ----------
def test_changing_the_config_changes_the_score(monkeypatch):
    monkeypatch.setitem(cfg.SEVERITY_BY_CATEGORY, "Other", 25)
    assert pts(calculate_risk("Other"), "severity") == 25


def test_function_cannot_see_privacy_mode_or_identity():
    params = inspect.signature(calculate_risk).parameters
    for banned in ("privacy_mode", "user_id", "user", "identity", "pseudonym", "status"):
        assert banned not in params