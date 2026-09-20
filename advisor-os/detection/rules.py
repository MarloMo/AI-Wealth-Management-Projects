"""Deterministic detection rules for Advisor OS development.

Standard library only. Computes explainable findings from synthetic client
and portfolio data. Does not provide or implement financial advice.
"""

from __future__ import annotations

CONCENTRATION_THRESHOLD = 0.40
CASH_WEIGHT_THRESHOLD = 0.10
RETIREMENT_HORIZON_YEARS = 3

URGENCY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _portfolio_total(portfolio: dict) -> float:
    return float(sum(holding["current_value"] for holding in portfolio["holdings"]))


def _cash_value(portfolio: dict) -> float:
    cash_total = 0.0
    for holding in portfolio["holdings"]:
        if holding.get("asset_class") == "Cash" or holding.get("ticker") == "CASH":
            cash_total += float(holding["current_value"])
    return cash_total


def detect_concentration(client: dict, portfolio: dict) -> dict | None:
    total = _portfolio_total(portfolio)
    if total <= 0:
        return None

    top_holding = max(portfolio["holdings"], key=lambda item: item["current_value"])
    weight = float(top_holding["current_value"]) / total
    if weight <= CONCENTRATION_THRESHOLD:
        return None

    return {
        "finding_id": f"{client['client_id']}-R001",
        "rule_id": "concentration_risk",
        "event_type": "concentration_risk",
        "urgency": "high",
        "summary": (
            f"{top_holding['ticker']} is {weight:.0%} of investable assets, "
            f"above the {CONCENTRATION_THRESHOLD:.0%} concentration threshold."
        ),
        "rationale": (
            "Single-position weight exceeds the configured concentration threshold."
        ),
        "evidence": {
            "ticker": top_holding["ticker"],
            "holding_value": top_holding["current_value"],
            "portfolio_value": total,
            "weight": round(weight, 4),
            "threshold": CONCENTRATION_THRESHOLD,
        },
        "confidence": 0.95,
        "suggested_next_action": (
            "Review single-position exposure with the client and discuss "
            "whether diversification is appropriate."
        ),
    }


def detect_retirement_horizon(client: dict, portfolio: dict) -> dict | None:
    del portfolio  # portfolio unused; signature kept consistent across rules
    age = int(client["age"])
    expected = int(client["form"]["occupation"]["expected_retirement_age"])
    years = expected - age
    if years > RETIREMENT_HORIZON_YEARS:
        return None

    return {
        "finding_id": f"{client['client_id']}-R002",
        "rule_id": "retirement_horizon",
        "event_type": "retirement_horizon",
        "urgency": "medium",
        "summary": (
            f"Client is {years} year(s) from expected retirement age {expected}."
        ),
        "rationale": (
            "Expected retirement is within the near-term planning horizon."
        ),
        "evidence": {
            "age": age,
            "expected_retirement_age": expected,
            "years_to_retirement": years,
            "threshold_years": RETIREMENT_HORIZON_YEARS,
        },
        "confidence": 0.90,
        "suggested_next_action": (
            "Schedule a near-retirement planning conversation covering income, "
            "Social Security timing, and spending goals."
        ),
    }


def detect_elevated_cash(client: dict, portfolio: dict) -> dict | None:
    total = _portfolio_total(portfolio)
    if total <= 0:
        return None

    cash = _cash_value(portfolio)
    weight = cash / total
    objective = client["form"]["money"]["investment_objective"]
    if weight <= CASH_WEIGHT_THRESHOLD:
        return None

    return {
        "finding_id": f"{client['client_id']}-R003",
        "rule_id": "elevated_cash",
        "event_type": "elevated_cash",
        "urgency": "medium",
        "summary": (
            f"Cash is {weight:.0%} of the portfolio, above the "
            f"{CASH_WEIGHT_THRESHOLD:.0%} cash-weight threshold."
        ),
        "rationale": (
            "Cash weight is elevated relative to the stated investment objective."
        ),
        "evidence": {
            "cash": cash,
            "portfolio_value": total,
            "cash_weight": round(weight, 4),
            "threshold": CASH_WEIGHT_THRESHOLD,
            "investment_objective": objective,
        },
        "confidence": 0.85,
        "suggested_next_action": (
            "Confirm whether the cash balance is intentional reserves or "
            f"awaiting deployment under the {objective} objective."
        ),
    }


def detect_planning_opportunity(client: dict, portfolio: dict) -> dict | None:
    del portfolio
    recreation = client["form"]["recreation"]
    goal = recreation.get("retirement_goal")
    if not goal:
        return None

    return {
        "finding_id": f"{client['client_id']}-R004",
        "rule_id": "planning_opportunity",
        "event_type": "planning_opportunity",
        "urgency": "low",
        "summary": (
            f"Retirement goal noted: {goal}. Review income and liquidity needs."
        ),
        "rationale": (
            "A stated retirement goal creates a planning conversation opportunity."
        ),
        "evidence": {
            "retirement_goal": goal,
            "interests": recreation.get("interests", []),
        },
        "confidence": 0.70,
        "suggested_next_action": (
            f"Incorporate the retirement goal ({goal}) into the next meeting "
            "agenda and estimate liquidity needs."
        ),
    }


RULES = [
    detect_concentration,
    detect_retirement_horizon,
    detect_elevated_cash,
    detect_planning_opportunity,
]


def run_rules(client: dict, portfolio: dict) -> list[dict]:
    """Run all detection rules and return ranked findings for one client."""
    if client["client_id"] != portfolio["client_id"]:
        raise ValueError(
            "client_id mismatch between client "
            f"({client['client_id']}) and portfolio ({portfolio['client_id']})."
        )

    findings = []
    for rule in RULES:
        result = rule(client, portfolio)
        if result is not None:
            findings.append(result)

    findings.sort(key=lambda item: URGENCY_ORDER.get(item["urgency"], 99))
    return findings
