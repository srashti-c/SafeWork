"""SafeWork retaliation flag (Phase 6).

check_retaliation(complaint_date, events) returns a flag when a recorded adverse
employment event (for example demotion, transfer, suspension) happened within the
time window after the complaint was filed. It is a prompt for a HUMAN reviewer. It
never decides that retaliation happened.

All settings (window, allowed event types, notice text) live in pattern_config.py.
Pure function: no database, no API. The caller passes the recorded events.
"""
from datetime import date, datetime

from app.services import pattern_config as cfg


def _to_date(value, name):
    if isinstance(value, datetime):      # check datetime first (it is also a date)
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError(name + " must be a date")


def check_retaliation(complaint_date, events, window_days=None):
    """complaint_date: the date the complaint was FILED (date or datetime).
    events: list of {"event_type": one of cfg.ADVERSE_EVENT_TYPES,
                     "event_date": date or datetime}.
    window_days: optional override of cfg.RETALIATION_WINDOW_DAYS (whole number, 1 or more).

    An event counts when 0 <= (event_date - complaint_date) <= window_days
    (same day counts; events before the complaint never count).

    Returns a dict:
      retaliation_flag: True or False
      window_days, events_checked
      matches: list of {event_type, event_date (YYYY-MM-DD), days_after}, earliest first
      notice (always present = cfg.RETALIATION_NOTICE), message
    Bad input raises ValueError (never a silent guess)."""
    window = cfg.RETALIATION_WINDOW_DAYS if window_days is None else window_days
    if not isinstance(window, int) or isinstance(window, bool) or window < 1:
        raise ValueError("window_days must be a whole number of 1 or more")
    filed = _to_date(complaint_date, "complaint_date")
    if not isinstance(events, (list, tuple)):
        raise ValueError("events must be a list")

    matches = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("every event must be a dict")
        kind = event.get("event_type")
        if not isinstance(kind, str) or kind.strip().lower() not in cfg.ADVERSE_EVENT_TYPES:
            raise ValueError("event_type must be one of: " + ", ".join(cfg.ADVERSE_EVENT_TYPES))
        happened = _to_date(event.get("event_date"), "event_date")
        days_after = (happened - filed).days
        if 0 <= days_after <= window:
            matches.append({"event_type": kind.strip().lower(),
                            "event_date": happened.isoformat(),
                            "days_after": days_after})
    matches.sort(key=lambda m: (m["event_date"], m["event_type"]))

    flag = len(matches) > 0
    if flag:
        message = (str(len(matches)) + " adverse event(s) were recorded within "
                   + str(window) + " days after the complaint was filed. "
                   "A human reviewer should look at this.")
    else:
        message = ("No adverse event is recorded within " + str(window) + " days after the "
                   "complaint was filed. Only recorded events are checked, so this does "
                   "not prove there was none.")
    return {"retaliation_flag": flag, "window_days": window,
            "events_checked": len(events), "matches": matches,
            "notice": cfg.RETALIATION_NOTICE, "message": message}