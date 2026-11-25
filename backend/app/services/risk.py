"""Explainable, rule-weighted risk score (Phase 5).
Pure function: no database, no API, no NLP model. All numbers come from
risk_config.py. It returns the score AND the reason for every point.
It never looks at privacy mode, status, or who filed the complaint.
"""
import re

from app.services import risk_config as cfg


def level_for_score(score):
    """Return LOW / MEDIUM / HIGH / CRITICAL for a score."""
    for cutoff, name in sorted(cfg.LEVEL_CUTOFFS, reverse=True):
        if score >= cutoff:
            return name
    return min(cfg.LEVEL_CUTOFFS)[1]


def _find_threats(text):
    t = text.lower().replace("\u2019", "'")
    return [p for p in cfg.THREAT_PHRASES if re.search(r"\b" + re.escape(p), t)]


def _count(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(name + " must be a whole number, 0 or more")
    return value


def _reason(factor, points, why):
    return {
        "factor": factor,
        "points": points,
        "max_points": cfg.MAX_POINTS[factor],
        "reason": why,
    }


def calculate_risk(
    category_name,
    text="",
    frequency="unknown",
    power_imbalance="unknown",
    retaliation_flag=False,
    recurrence_count=0,
    evidence_count=0,
):
    if frequency not in cfg.FREQUENCY_POINTS:
        raise ValueError("frequency must be one of: " + ", ".join(cfg.FREQUENCY_POINTS))
    if power_imbalance not in cfg.POWER_POINTS:
        raise ValueError("power_imbalance must be one of: " + ", ".join(cfg.POWER_POINTS))
    recurrence_count = _count("recurrence_count", recurrence_count)
    evidence_count = _count("evidence_count", evidence_count)
    if not isinstance(text, str):
        text = ""

    reasons = []

    # 1. severity (from the category name)
    lookup = {k.lower(): v for k, v in cfg.SEVERITY_BY_CATEGORY.items()}
    key = category_name.strip().lower() if isinstance(category_name, str) else ""
    if key in lookup:
        reasons.append(_reason("severity", lookup[key],
                               "Category '" + category_name.strip() + "' has this severity weight."))
    else:
        reasons.append(_reason("severity", 0,
                               "Category not recognised, so 0 points. A reviewer should check it."))

    # 2. frequency
    reasons.append(_reason("frequency", cfg.FREQUENCY_POINTS[frequency],
                           "Frequency given as '" + frequency + "'."))

    # 3. power imbalance
    reasons.append(_reason("power_imbalance", cfg.POWER_POINTS[power_imbalance],
                           "Power imbalance given as '" + power_imbalance + "'."))

    # 4. threat language
    found = _find_threats(text)
    if len(found) >= 2:
        reasons.append(_reason("threat_language", cfg.THREAT_POINTS_MANY_MATCHES,
                               "Threat phrases found: " + ", ".join(found) + "."))
    elif len(found) == 1:
        reasons.append(_reason("threat_language", cfg.THREAT_POINTS_ONE_MATCH,
                               "Threat phrase found: " + found[0] + "."))
    else:
        reasons.append(_reason("threat_language", 0, "No listed threat phrase found in the text."))

    # 5. retaliation flag
    if retaliation_flag:
        reasons.append(_reason("retaliation", cfg.RETALIATION_POINTS,
                               "Retaliation flag is ON (a human should review it)."))
    else:
        reasons.append(_reason("retaliation", 0, "Retaliation flag is off."))

    # 6. recurrence
    if recurrence_count >= 2:
        reasons.append(_reason("recurrence", cfg.RECURRENCE_POINTS_MANY,
                               str(recurrence_count) + " earlier similar cases."))
    elif recurrence_count == 1:
        reasons.append(_reason("recurrence", cfg.RECURRENCE_POINTS_ONE,
                               "1 earlier similar case."))
    else:
        reasons.append(_reason("recurrence", 0, "No earlier similar case counted."))

    # 7. evidence
    if evidence_count >= 2:
        reasons.append(_reason("evidence", cfg.EVIDENCE_POINTS_MANY,
                               str(evidence_count) + " evidence files attached."))
    elif evidence_count == 1:
        reasons.append(_reason("evidence", cfg.EVIDENCE_POINTS_ONE,
                               "1 evidence file attached."))
    else:
        reasons.append(_reason("evidence", 0, "No evidence file attached."))

    score = min(sum(r["points"] for r in reasons), sum(cfg.MAX_POINTS.values()))
    return {
        "score": score,
        "max_score": sum(cfg.MAX_POINTS.values()),
        "level": level_for_score(score),
        "reasons": reasons,
        "notice": cfg.NOTICE,
    }