"""SafeWork risk score - ALL settings live in this one file.
Change a number here and the score changes. Nothing else needs editing.

The score is a PRIORITY for human reviewers. It is NOT a probability of guilt.
The weights below are design choices by the project author. They were NOT tuned
on real complaint data.
"""

# Most points each factor can add. They add up to 100.
MAX_POINTS = {
    "severity": 30,
    "frequency": 15,
    "power_imbalance": 15,
    "threat_language": 15,
    "retaliation": 10,
    "recurrence": 10,
    "evidence": 5,
}

# Severity comes from the category NAME (same names as seed_categories.py).
SEVERITY_BY_CATEGORY = {
    "Physical harassment": 30,
    "Sexual harassment": 30,
    "Discrimination": 20,
    "Retaliation": 20,
    "Bullying / abuse of power": 15,
    "Verbal harassment": 12,
    "Other": 3,
}

# How often did it happen? (the reviewer gives this)
FREQUENCY_POINTS = {
    "unknown": 0,
    "once": 0,
    "a_few": 8,
    "repeated": 15,
}

# Power gap between the two people (the reviewer gives this)
POWER_POINTS = {
    "unknown": 0,
    "none": 0,
    "senior": 10,
    "direct_manager": 15,
}

# Threat language: simple phrase matching on the complaint text.
THREAT_POINTS_ONE_MATCH = 8
THREAT_POINTS_MANY_MATCHES = 15      # 2 or more different phrases found
THREAT_PHRASES = [
    "kill you", "hurt you", "beat you", "fire you", "get you fired",
    "you will regret", "you'll regret", "ruin your career",
    "destroy your career", "if you tell", "if you complain",
    "if you report", "no one will believe", "make your life hell",
    "teach you a lesson", "i will find you", "blackmail", "leak your",
]

# Retaliation flag (Phase 6 will set it; Phase 5 only accepts it)
RETALIATION_POINTS = 10

# Recurrence = how many earlier similar cases (Phase 6 will count them)
RECURRENCE_POINTS_ONE = 5
RECURRENCE_POINTS_MANY = 10          # 2 or more

# Evidence = number of evidence files attached
EVIDENCE_POINTS_ONE = 3
EVIDENCE_POINTS_MANY = 5             # 2 or more

# Level cut-offs: a score at or above the number gets that level.
LEVEL_CUTOFFS = [
    (75, "CRITICAL"),
    (50, "HIGH"),
    (25, "MEDIUM"),
    (0, "LOW"),
]

NOTICE = (
    "PRIORITY ONLY, for a human reviewer. This score only ranks which cases "
    "to look at first. It is NOT a probability of guilt, it does NOT decide "
    "what happened or who is at fault, and it must never replace the "
    "judgement of the Internal Committee."
)