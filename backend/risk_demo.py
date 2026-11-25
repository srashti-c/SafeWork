"""Small demo for the viva. Run from the backend folder: python risk_demo.py"""
import json

from app.services.risk import calculate_risk

result = calculate_risk(
    "Bullying / abuse of power",
    text="My manager said if you complain I will ruin your career.",
    frequency="a_few",
    power_imbalance="direct_manager",
    evidence_count=1,
)
print(json.dumps(result, indent=2))