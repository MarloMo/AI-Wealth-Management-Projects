"""Deterministic IPS draft engine. No live market data. No advice."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "model_portfolios.csv"

CATEGORIES = ("Conservative", "Moderate", "Aggressive")

# Transparent scoring. Documented in README. Not a suitability engine.
HORIZON_POINTS = {
    "Under 5 years": 0,
    "5–10 years": 1,
    "10–20 years": 2,
    "20+ years": 3,
}
TOLERANCE_POINTS = {
    "Low — protect principal": 0,
    "Medium — some ups and downs": 1,
    "High — large swings are acceptable": 2,
}
LIQUIDITY_POINTS = {
    "Need cash in under 2 years": 0,
    "Might need some cash in 2–5 years": 1,
    "Unlikely to need this money for 5+ years": 2,
}


@dataclass(frozen=True)
class InvestorInput:
    name: str
    goal: str
    horizon: str
    liquidity: str
    tolerance: str


@dataclass(frozen=True)
class Draft:
    category: str
    stocks_pct: int
    bonds_pct: int
    cash_pct: int
    score: int
    score_breakdown: str
    ips_text: str


def score_investor(inp: InvestorInput) -> tuple[int, str]:
    h = HORIZON_POINTS[inp.horizon]
    t = TOLERANCE_POINTS[inp.tolerance]
    l = LIQUIDITY_POINTS[inp.liquidity]
    total = h + t + l
    breakdown = (
        f"Time horizon ({inp.horizon}): {h} pts. "
        f"Risk tolerance ({inp.tolerance}): {t} pts. "
        f"Liquidity ({inp.liquidity}): {l} pts. "
        f"Total {total} / 7."
    )
    return total, breakdown


def category_from_score(score: int) -> str:
    if score <= 2:
        return "Conservative"
    if score <= 4:
        return "Moderate"
    return "Aggressive"


def load_allocations(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(CATEGORIES) - set(df["risk_category"])
    if missing:
        raise ValueError(f"model_portfolios.csv missing categories: {missing}")
    return df.set_index("risk_category")


def build_draft(inp: InvestorInput, allocations: pd.DataFrame | None = None) -> Draft:
    if allocations is None:
        allocations = load_allocations()
    score, breakdown = score_investor(inp)
    category = category_from_score(score)
    row = allocations.loc[category]
    stocks, bonds, cash = int(row["stocks_pct"]), int(row["bonds_pct"]), int(row["cash_pct"])
    ips = (
        f"HYPOTHETICAL INVESTMENT POLICY SUMMARY (DRAFT)\n"
        f"{'=' * 48}\n\n"
        f"Investor (fictional): {inp.name}\n"
        f"Stated goal: {inp.goal}\n"
        f"Time horizon: {inp.horizon}\n"
        f"Liquidity need: {inp.liquidity}\n"
        f"Stated risk tolerance: {inp.tolerance}\n\n"
        f"Proposed risk category: {category}\n"
        f"Scoring (not a suitability determination): {breakdown}\n\n"
        f"Proposed model allocation:\n"
        f"  Stocks {stocks}%  |  Bonds {bonds}%  |  Cash {cash}%\n\n"
        f"This draft maps a stated profile to a preset model mix. "
        f"It does not analyze a real portfolio, tax situation, or legal constraints. "
        f"It is not a recommendation and is not investment advice. "
        f"A licensed advisor must review and approve before any real-world use.\n\n"
        f"Status: PENDING HUMAN APPROVAL\n"
    )
    return Draft(
        category=category,
        stocks_pct=stocks,
        bonds_pct=bonds,
        cash_pct=cash,
        score=score,
        score_breakdown=breakdown,
        ips_text=ips,
    )


def approved_packet(draft: Draft) -> str:
    return draft.ips_text.replace(
        "Status: PENDING HUMAN APPROVAL",
        "Status: APPROVED BY HUMAN REVIEWER (demo only)",
    )


JORDAN_HALE = InvestorInput(
    name="Jordan Hale (fictional)",
    goal="Retirement income in about 18 years",
    horizon="10–20 years",
    liquidity="Unlikely to need this money for 5+ years",
    tolerance="Medium — some ups and downs",
)
