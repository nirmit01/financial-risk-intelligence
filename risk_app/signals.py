"""Translate analyzed text into transparent portfolio stress suggestions."""
from .portfolio import SCENARIOS

EVENT_TO_SCENARIO = {
    "Geopolitical": "Geopolitical escalation",
    "Macroeconomic": "Inflation / rate shock",
    "Credit Event": "Credit crisis",
    "Market / Liquidity": "Market liquidity shock",
}
def generate_risk_signal(analysis: dict) -> dict:
    event = analysis.get("event_type", "Other")
    impact = int(analysis.get("impact", 1))
    scenario = EVENT_TO_SCENARIO.get(event)
    if not scenario and impact >= 7:
        scenario = "Market liquidity shock"
    return {
        "event_type": event, "impact": impact, "scenario": scenario,
        "priority": "High" if impact >= 7 else ("Medium" if impact >= 4 else "Low"),
        "suggested_severity": round(min(2.0, max(0.5, impact / 5)), 1),
        "reason": f"{event} event with impact score {impact}/10",
    }
