"""Small demo for the viva: runs the REAL MiniLM model on 3 made-up cases.
Run from the backend folder (venv active):  python pattern_demo.py
"""
from datetime import datetime, timedelta, timezone

from app.services.pattern import find_similar_cases
from app.services.retaliation import check_retaliation

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
cases = [
    {"id": "case-1", "title": "Manager shouting", "category": "Verbal harassment",
     "description": "My manager shouts at me in front of the team every week.",
     "created_at": T0},
    {"id": "case-2", "title": "Shouted at in meetings", "category": "Verbal harassment",
     "description": "My supervisor yells at me in meetings in front of colleagues.",
     "created_at": T0 + timedelta(days=20)},
    {"id": "case-3", "title": "Canteen", "category": "Other",
     "description": "The canteen food is cold and the AC in my room is broken.",
     "created_at": T0 + timedelta(days=30)},
]

print("ALL pair scores (threshold 0 shows everything):")
for p in find_similar_cases(cases, threshold=0)["pairs"]:
    print("  ", p["case_a"], p["case_b"], p["similarity"])

r = find_similar_cases(cases)
print()
print("With the configured threshold", r["threshold"], "->", r["message"])
print(r["notice"])

event = {"event_type": "transfer", "event_date": (T0 + timedelta(days=40)).date()}
c = check_retaliation(cases[0]["created_at"], [event])
print()
print(c["message"])
print(c["notice"])