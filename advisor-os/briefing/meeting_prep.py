"""Meeting-prep stub for Advisor OS development.

Builds a simple advisor meeting agenda from rule-detected briefing findings.
Standard library only. Does not provide or implement financial advice.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))

from generate_briefing import generate_briefing
from synthetic_clients import clients

DOCS_TO_BRING = [
    "Current holdings summary",
    "Last risk questionnaire",
    "Most recent financial plan / retirement projection (if any)",
]


def generate_meeting_prep(client_id: str = "C001") -> dict:
    briefing = generate_briefing(client_id)
    client_info = briefing["client"]

    agenda = []
    for index, finding in enumerate(briefing["findings"], start=1):
        agenda.append(
            {
                "item_number": index,
                "urgency": finding["urgency"],
                "finding_id": finding["finding_id"],
                "topic": finding["summary"],
                "discussion_prompt": finding["suggested_next_action"],
                "evidence": finding["evidence"],
            }
        )

    return {
        "meeting_prep_id": f"MP-{client_id}-001",
        "as_of_date": briefing["as_of_date"],
        "client": {
            "client_id": client_info["client_id"],
            "name": client_info["name"],
            "age": client_info["age"],
            "risk_profile": client_info["risk_profile"],
            "investment_objective": client_info["investment_objective"],
        },
        "agenda": agenda,
        "docs_to_bring": list(DOCS_TO_BRING),
        "disclaimer": (
            "Synthetic meeting-prep stub for Advisor OS development. "
            "Not investment advice. Requires advisor review."
        ),
    }


def format_meeting_prep(meeting_prep: dict) -> str:
    client_info = meeting_prep["client"]
    lines = [
        f"Meeting prep — {client_info['name']} ({client_info['client_id']})",
        f"Prep ID: {meeting_prep['meeting_prep_id']}",
        f"As of: {meeting_prep['as_of_date']}",
        f"Age: {client_info['age']} | Risk: {client_info['risk_profile']} | "
        f"Objective: {client_info['investment_objective']}",
        "",
        "Agenda",
    ]

    if not meeting_prep["agenda"]:
        lines.extend(["", "No agenda items — no rule findings for this client."])

    for item in meeting_prep["agenda"]:
        lines.extend(
            [
                "",
                f"{item['item_number']}. [{item['urgency'].upper()}] {item['topic']}",
                f"   Discuss: {item['discussion_prompt']}",
                f"   Finding: {item['finding_id']}",
            ]
        )

    lines.extend(["", "Docs to bring"])
    for doc in meeting_prep["docs_to_bring"]:
        lines.append(f"- {doc}")

    lines.extend(["", meeting_prep["disclaimer"]])
    return "\n".join(lines)


if __name__ == "__main__":
    selected = sys.argv[1] if len(sys.argv) > 1 else "all"
    if selected == "all":
        for client_id in clients:
            print(format_meeting_prep(generate_meeting_prep(client_id)))
            print("\n" + ("-" * 60) + "\n")
    else:
        print(format_meeting_prep(generate_meeting_prep(selected)))
