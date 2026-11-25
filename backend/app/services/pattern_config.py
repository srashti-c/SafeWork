"""SafeWork pattern alerts + retaliation flag - ALL settings live in this one file.
Change a number here and the behaviour changes. Nothing else needs editing.

Both tools only PROMPT a human reviewer. They never name, accuse or identify anyone
and never decide what happened. The numbers are design choices by the project author.
The similarity threshold is set from a measurement on SYNTHETIC data
(see ml/threshold_study.py and PROJECT_CONTEXT.md).
"""

# Pattern alerts: two complaints count as "similar" if their text similarity (0 to 1)
# is AT OR ABOVE this number.  MEASURED on SYNTHETIC data (ml/threshold_study.py): lowest value with precision >= 0.90.
SIMILARITY_THRESHOLD = 0.71

# Retaliation flag: an adverse event counts if it was recorded 0 to N days
# (both included) after the day the complaint was filed.
RETALIATION_WINDOW_DAYS = 90

# Same sentence-transformer as Phase 4 (ml/common.py EMBED_MODEL).
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# Longer text is cut to this many characters (keeps things fast and safe).
MAX_TEXT_CHARS = 5000

# Allowed kinds of adverse employment event (a fixed list on purpose: no free text, no names).
ADVERSE_EVENT_TYPES = [
    "termination",
    "demotion",
    "transfer",
    "suspension",
    "pay_cut",
    "denied_promotion",
    "negative_review",
    "schedule_change",
    "other",
]

PATTERN_NOTICE = (
    "FOR HUMAN REVIEW ONLY. These cases have similar wording. Similar wording does NOT "
    "mean the same person, the same incident or any wrongdoing. This tool does NOT name, "
    "accuse or identify anyone, and it does NOT decide what happened. A human reviewer "
    "must read the cases. Only the Internal Committee decides."
)

RETALIATION_NOTICE = (
    "PROMPT FOR HUMAN REVIEW ONLY. A flag means an adverse employment event was recorded "
    "within the time window after the complaint was filed. This does NOT mean retaliation "
    "happened, and it does NOT decide who is at fault: events can have other reasons. "
    "No flag does NOT mean there was no retaliation, because only recorded events are "
    "checked. A human reviewer and the Internal Committee must look at the facts."
)