"""Gives the Phase 5 risk score its two inputs (Phase 6).

Usage:  r = risk_inputs_for(case_id, cases, events)
        calculate_risk(category_name, text, **r["inputs"])
'inputs' has exactly the two names Phase 5 accepts: retaliation_flag, recurrence_count.
risk.py and risk_config.py are NOT changed. The full pattern and retaliation results
(with their notices) are returned too, so a screen can show them to a human reviewer.
Note: recurrence counts only EARLIER similar cases; 'similar_cases' lists all similar ones.
"""
from app.services import pattern, retaliation
from app.services import pattern_config as cfg


def risk_inputs_for(case_id, cases, events, embedder=None, threshold=None, window_days=None):
    filed = pattern.filed_at_of(case_id, cases)
    ret = retaliation.check_retaliation(filed, events, window_days)
    similar = pattern.similar_to(case_id, cases, embedder, threshold)
    count = pattern.recurrence_count(case_id, cases, embedder, threshold)
    return {
        "inputs": {"retaliation_flag": ret["retaliation_flag"], "recurrence_count": count},
        "retaliation": ret,
        "similar_cases": similar,
        "notice": cfg.PATTERN_NOTICE + "\n" + cfg.RETALIATION_NOTICE,
    }