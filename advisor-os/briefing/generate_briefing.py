"""Generate a first-pass explainable advisor briefing for one client.

Standard library only. Reads synthetic client and portfolio data, runs
deterministic detection rules, then ranks findings for advisor review.
Does not provide or implement advice.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "detection"))

from rules import run_rules
from synthetic_clients import clients
from synthetic_portfolio import portfolios


def generate_briefing(client_id: str = "C001") -> dict:
    if client_id not in clients:
        raise ValueError(f"Synthetic client {client_id} not found.")
    if client_id not in portfolios:
        raise ValueError(f"Synthetic portfolio for {client_id} not found.")

    client = clients[client_id]
    portfolio = portfolios[client_id]
    money = client["form"]["money"]
    holdings_total = sum(h["current_value"] for h in portfolio["holdings"])
    findings = run_rules(client, portfolio)

    return {
        "briefing_id": f"B-{client_id}-001",
        "as_of_date": portfolio["as_of_date"],
        "client": {
            "client_id": client["client_id"],
            "name": client["name"],
            "age": client["age"],
            "risk_profile": money["risk_profile"],
            "investment_objective": money["investment_objective"],
            "total_investable_assets": money["total_investable_assets"],
            "cash": money["cash"],
            "portfolio_current_value": holdings_total,
        },
        "findings": findings,
        "disclaimer": (
            "Synthetic research output for Advisor OS development. "
            "Not investment advice. Requires advisor review."
        ),
    }


def format_briefing(briefing: dict) -> str:
    client_info = briefing["client"]
    lines = [
        f"Advisor Briefing {briefing['briefing_id']}",
        f"As of: {briefing['as_of_date']}",
        "",
        f"Client: {client_info['name']} ({client_info['client_id']})",
        f"Age: {client_info['age']}",
        f"Risk profile: {client_info['risk_profile']}",
        f"Objective: {client_info['investment_objective']}",
        f"Investable assets: ${client_info['total_investable_assets']:,}",
        f"Cash: ${client_info['cash']:,}",
        f"Portfolio value: ${client_info['portfolio_current_value']:,}",
        "",
        "Prioritized findings (rule-detected):",
    ]

    if not briefing["findings"]:
        lines.extend(["", "No rule findings for this client."])

    for index, finding in enumerate(briefing["findings"], start=1):
        lines.extend(
            [
                "",
                f"{index}. [{finding['urgency'].upper()}] {finding['summary']}",
                f"   Finding ID: {finding['finding_id']} ({finding['rule_id']})",
                f"   Evidence: {finding['evidence']}",
                f"   Confidence: {finding['confidence']:.2f}",
                f"   Suggested next action: {finding['suggested_next_action']}",
            ]
        )

    lines.extend(["", briefing["disclaimer"]])
    return "\n".join(lines)


if __name__ == "__main__":
    selected = sys.argv[1] if len(sys.argv) > 1 else "all"
    if selected == "all":
        for client_id in clients:
            print(format_briefing(generate_briefing(client_id)))
            print("\n" + ("-" * 60) + "\n")
    else:
        print(format_briefing(generate_briefing(selected)))
