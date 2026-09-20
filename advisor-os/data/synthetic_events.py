"""Synthetic client events for Advisor OS development."""

events = [
    {
        "event_id": "E001",
        "client_id": "C001",
        "event_type": "concentration_risk",
        "as_of_date": "2026-09-01",
        "urgency": "high",
        "summary": "Single holding exceeds 40% of investable assets.",
        "details": {
            "ticker": "VTI",
            "holding_value": 400000,
            "portfolio_value": 850000,
            "weight": 0.47,
            "threshold": 0.40,
        },
    },
    {
        "event_id": "E002",
        "client_id": "C001",
        "event_type": "retirement_horizon",
        "as_of_date": "2026-09-01",
        "urgency": "medium",
        "summary": "Client is within 3 years of expected retirement.",
        "details": {
            "age": 62,
            "expected_retirement_age": 65,
            "years_to_retirement": 3,
        },
    },
    {
        "event_id": "E003",
        "client_id": "C001",
        "event_type": "elevated_cash",
        "as_of_date": "2026-09-01",
        "urgency": "medium",
        "summary": "Cash balance is elevated relative to the growth-and-income objective.",
        "details": {
            "cash": 125000,
            "portfolio_value": 850000,
            "cash_weight": 0.15,
            "investment_objective": "Growth and Income",
        },
    },
    {
        "event_id": "E004",
        "client_id": "C001",
        "event_type": "planning_opportunity",
        "as_of_date": "2026-09-01",
        "urgency": "low",
        "summary": "Retirement goal includes international travel; review income and liquidity plan.",
        "details": {
            "retirement_goal": "Travel internationally",
            "interests": ["Golf", "Travel"],
        },
    },
]
