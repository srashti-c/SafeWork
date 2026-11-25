"""Tests for Phase 6 retaliation flag (pure function, no database)."""
from datetime import date, datetime

import pytest

from app.services import pattern_config as cfg
from app.services.retaliation import check_retaliation

FILED = date(2026, 3, 1)


def ev(kind, day):
    return {"event_type": kind, "event_date": day}


def test_event_inside_window_is_flagged():
    r = check_retaliation(FILED, [ev("demotion", date(2026, 4, 1))])
    assert r["retaliation_flag"] is True
    assert r["matches"] == [{"event_type": "demotion", "event_date": "2026-04-01",
                             "days_after": 31}]


def test_no_events_not_flagged():
    r = check_retaliation(FILED, [])
    assert r["retaliation_flag"] is False
    assert r["matches"] == [] and r["events_checked"] == 0


def test_event_before_complaint_never_counts():
    r = check_retaliation(FILED, [ev("termination", date(2026, 2, 28))])
    assert r["retaliation_flag"] is False


def test_same_day_counts():
    r = check_retaliation(FILED, [ev("suspension", FILED)])
    assert r["retaliation_flag"] is True and r["matches"][0]["days_after"] == 0


def test_last_day_of_window_counts_next_day_does_not():
    last = date.fromordinal(FILED.toordinal() + cfg.RETALIATION_WINDOW_DAYS)
    after = date.fromordinal(last.toordinal() + 1)
    assert check_retaliation(FILED, [ev("transfer", last)])["retaliation_flag"] is True
    assert check_retaliation(FILED, [ev("transfer", after)])["retaliation_flag"] is False


def test_custom_window_overrides_config():
    e = [ev("pay_cut", date(2026, 3, 20))]            # 19 days after
    assert check_retaliation(FILED, e, window_days=30)["retaliation_flag"] is True
    assert check_retaliation(FILED, e, window_days=10)["retaliation_flag"] is False
    assert check_retaliation(FILED, e, window_days=10)["window_days"] == 10


def test_config_change_changes_result(monkeypatch):
    e = [ev("schedule_change", date(2026, 3, 20))]
    monkeypatch.setattr(cfg, "RETALIATION_WINDOW_DAYS", 5)
    assert check_retaliation(FILED, e)["retaliation_flag"] is False


def test_only_events_in_window_are_listed_earliest_first():
    events = [ev("suspension", date(2026, 4, 10)), ev("transfer", date(2026, 3, 5)),
              ev("termination", date(2026, 9, 1)), ev("demotion", date(2026, 2, 1))]
    r = check_retaliation(FILED, events)
    assert [m["event_type"] for m in r["matches"]] == ["transfer", "suspension"]
    assert r["events_checked"] == 4


def test_datetime_inputs_are_accepted():
    r = check_retaliation(datetime(2026, 3, 1, 23, 59),
                          [ev("suspension", datetime(2026, 3, 2, 0, 1))])
    assert r["retaliation_flag"] is True and r["matches"][0]["days_after"] == 1


def test_event_type_is_case_and_space_tolerant():
    r = check_retaliation(FILED, [ev("  Demotion ", date(2026, 3, 2))])
    assert r["matches"][0]["event_type"] == "demotion"


@pytest.mark.parametrize("bad", ["2026-03-01", None, 20260301, 1.5])
def test_bad_complaint_date_raises(bad):
    with pytest.raises(ValueError):
        check_retaliation(bad, [])


@pytest.mark.parametrize("bad", [None, "demotion", {"event_type": "demotion"}, 5])
def test_events_must_be_a_list(bad):
    with pytest.raises(ValueError):
        check_retaliation(FILED, bad)


@pytest.mark.parametrize("bad_event", [
    "demotion", None, {}, ev("fired_by_ghost", date(2026, 3, 2)),
    ev(None, date(2026, 3, 2)), ev(5, date(2026, 3, 2)),
    {"event_type": "demotion"}, ev("demotion", "2026-03-02"), ev("demotion", None),
])
def test_bad_event_raises(bad_event):
    with pytest.raises(ValueError):
        check_retaliation(FILED, [bad_event])


@pytest.mark.parametrize("bad", [0, -5, 1.5, True, "90"])
def test_bad_window_raises(bad):
    with pytest.raises(ValueError):
        check_retaliation(FILED, [], window_days=bad)


def test_notice_is_always_present_and_does_not_accuse():
    for events in ([], [ev("suspension", date(2026, 3, 2))]):
        r = check_retaliation(FILED, events)
        assert r["notice"] == cfg.RETALIATION_NOTICE
        assert "human reviewer" in r["notice"].lower()
        assert "does NOT mean retaliation happened" in r["notice"]
        assert "Internal Committee" in r["notice"]


def test_every_configured_event_type_is_accepted():
    for kind in cfg.ADVERSE_EVENT_TYPES:
        assert check_retaliation(FILED, [ev(kind, date(2026, 3, 2))])["retaliation_flag"] is True


def test_event_type_not_in_config_list_raises():
    for old_name in ("warning", "shift_change"):       # names that are NOT in pattern_config.py
        with pytest.raises(ValueError):
            check_retaliation(FILED, [ev(old_name, date(2026, 3, 2))])


def test_timezone_aware_datetime_is_accepted():
    from datetime import timezone
    r = check_retaliation(datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
                          [ev("transfer", datetime(2026, 3, 11, tzinfo=timezone.utc))])
    assert r["matches"][0]["days_after"] == 10


def test_input_events_are_not_changed():
    events = [ev("Suspension", date(2026, 3, 2))]
    check_retaliation(FILED, events)
    assert events == [{"event_type": "Suspension", "event_date": date(2026, 3, 2)}]


def test_works_with_risk_score():
    """The flag plugs into Phase 5: retaliation flag on adds the Phase 5 retaliation points."""
    from app.services.risk import calculate_risk
    flag = check_retaliation(FILED, [ev("demotion", date(2026, 3, 9))])["retaliation_flag"]
    on = calculate_risk("Other", retaliation_flag=flag)
    off = calculate_risk("Other", retaliation_flag=False)
    assert on["score"] > off["score"]