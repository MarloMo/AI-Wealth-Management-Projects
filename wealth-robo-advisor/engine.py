"""Deterministic IPS draft engine. No live market data. No advice."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "model_portfolios.csv"

CATEGORIES = ("Conservative", "Moderate", "Aggressive")
DEMO_VALUE = 100_000.0  # fictional dollars, for illustrations only

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

# Canned shocks. Not forecasts. Labels are demo names only.
STRESS_SCENARIOS = {
    "Equity selloff": {"stocks": -0.20, "bonds": 0.02, "cash": 0.0},
    "Rates shock": {"stocks": -0.05, "bonds": -0.08, "cash": 0.0},
    "Inflation scare": {"stocks": -0.10, "bonds": -0.06, "cash": 0.0},
}


@dataclass(frozen=True)
class InvestorInput:
    name: str
    goal: str
    horizon: str
    liquidity: str
    tolerance: str


@dataclass(frozen=True)
class Mix:
    stocks_pct: int
    bonds_pct: int
    cash_pct: int


@dataclass(frozen=True)
class Draft:
    category: str
    stocks_pct: int
    bonds_pct: int
    cash_pct: int
    score: int
    score_breakdown: str
    explanation: str
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


def explain_mix(inp: InvestorInput, category: str, mix: Mix) -> str:
    return (
        f"{inp.name} stated a goal of “{inp.goal}” with a {inp.horizon} horizon, "
        f"{inp.liquidity.lower()}, and {inp.tolerance.lower()}. "
        f"The point system maps that to {category}. "
        f"The matching model mix is {mix.stocks_pct}% stocks, "
        f"{mix.bonds_pct}% bonds, and {mix.cash_pct}% cash. "
        f"This is a preset mapping, not a personal recommendation."
    )


def build_draft(inp: InvestorInput, allocations: pd.DataFrame | None = None) -> Draft:
    if allocations is None:
        allocations = load_allocations()
    score, breakdown = score_investor(inp)
    category = category_from_score(score)
    row = allocations.loc[category]
    mix = Mix(int(row["stocks_pct"]), int(row["bonds_pct"]), int(row["cash_pct"]))
    explanation = explain_mix(inp, category, mix)
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
        f"  Stocks {mix.stocks_pct}%  |  Bonds {mix.bonds_pct}%  |  Cash {mix.cash_pct}%\n\n"
        f"Plain-language note:\n{explanation}\n\n"
        f"This draft maps a stated profile to a preset model mix. "
        f"It does not analyze a real portfolio, tax situation, or legal constraints. "
        f"It is not a recommendation and is not investment advice. "
        f"A licensed advisor must review and approve before any real-world use.\n\n"
        f"Status: PENDING HUMAN APPROVAL\n"
    )
    return Draft(
        category=category,
        stocks_pct=mix.stocks_pct,
        bonds_pct=mix.bonds_pct,
        cash_pct=mix.cash_pct,
        score=score,
        score_breakdown=breakdown,
        explanation=explanation,
        ips_text=ips,
    )


def rebalance_trades(
    current: Mix,
    target: Mix,
    portfolio_value: float = DEMO_VALUE,
) -> pd.DataFrame:
    """Dollar trades to move a fictional $portfolio_value from current mix to target."""
    rows = []
    for label, cur, tgt in (
        ("Stocks", current.stocks_pct, target.stocks_pct),
        ("Bonds", current.bonds_pct, target.bonds_pct),
        ("Cash", current.cash_pct, target.cash_pct),
    ):
        delta_pct = tgt - cur
        dollars = portfolio_value * delta_pct / 100.0
        if dollars > 0.5:
            action = f"Buy ${dollars:,.0f}"
        elif dollars < -0.5:
            action = f"Sell ${abs(dollars):,.0f}"
        else:
            action = "Hold"
        rows.append(
            {
                "sleeve": label,
                "current_pct": cur,
                "target_pct": tgt,
                "drift_pct": delta_pct,
                "action": action,
            }
        )
    return pd.DataFrame(rows)


def stress_table(
    mix: Mix,
    portfolio_value: float = DEMO_VALUE,
) -> pd.DataFrame:
    """Apply canned shocks to the model mix. Not a risk model."""
    rows = []
    start = portfolio_value
    for name, shock in STRESS_SCENARIOS.items():
        end = start * (
            (mix.stocks_pct / 100.0) * (1 + shock["stocks"])
            + (mix.bonds_pct / 100.0) * (1 + shock["bonds"])
            + (mix.cash_pct / 100.0) * (1 + shock["cash"])
        )
        rows.append(
            {
                "scenario": name,
                "stock_shock": f"{shock['stocks']:+.0%}",
                "bond_shock": f"{shock['bonds']:+.0%}",
                "est_value": round(end),
                "est_change_pct": round((end / start - 1) * 100, 1),
            }
        )
    return pd.DataFrame(rows)


def v2_packet_text(draft: Draft, current: Mix, portfolio_value: float = DEMO_VALUE) -> str:
    target = Mix(draft.stocks_pct, draft.bonds_pct, draft.cash_pct)
    trades = rebalance_trades(current, target, portfolio_value)
    stress = stress_table(target, portfolio_value)
    lines = [
        "",
        "REBALANCE ILLUSTRATION (fictional dollars)",
        f"Assumed portfolio value: ${portfolio_value:,.0f}",
        f"Current mix: stocks {current.stocks_pct}% / bonds {current.bonds_pct}% / cash {current.cash_pct}%",
        trades.to_string(index=False),
        "",
        "MARKET STRESS ILLUSTRATION (canned shocks, not forecasts)",
        stress.to_string(index=False),
        "",
        "Stress and rebalance figures are arithmetic demos. They are not advice.",
    ]
    return "\n".join(str(x) for x in lines)


def approved_packet(
    draft: Draft,
    current: Mix | None = None,
    portfolio_value: float = DEMO_VALUE,
) -> str:
    text = draft.ips_text.replace(
        "Status: PENDING HUMAN APPROVAL",
        "Status: APPROVED BY HUMAN REVIEWER (demo only)",
    )
    if current is not None:
        text = text + "\n" + v2_packet_text(draft, current, portfolio_value)
    return text


JORDAN_HALE = InvestorInput(
    name="Jordan Hale (fictional)",
    goal="Retirement income in about 18 years",
    horizon="10–20 years",
    liquidity="Unlikely to need this money for 5+ years",
    tolerance="Medium — some ups and downs",
)

# Additional fictional samples so recruiters can compare sleeves.
# Scores: Avery 0 → Conservative, Casey 3 → Moderate, Jordan 5 → Aggressive, Riley 7 → Aggressive.
AVERY_NGUYEN = InvestorInput(
    name="Avery Nguyen (fictional)",
    goal="Keep a down-payment fund steady over the next few years",
    horizon="Under 5 years",
    liquidity="Need cash in under 2 years",
    tolerance="Low — protect principal",
)

CASEY_ORTIZ = InvestorInput(
    name="Casey Ortiz (fictional)",
    goal="Grow a taxable brokerage balance with moderate risk",
    horizon="5–10 years",
    liquidity="Might need some cash in 2–5 years",
    tolerance="Medium — some ups and downs",
)

RILEY_CHEN = InvestorInput(
    name="Riley Chen (fictional)",
    goal="Long-horizon retirement accumulation, comfortable with large swings",
    horizon="20+ years",
    liquidity="Unlikely to need this money for 5+ years",
    tolerance="High — large swings are acceptable",
)

SAMPLE_CLIENTS: dict[str, InvestorInput] = {
    "Avery Nguyen (Conservative)": AVERY_NGUYEN,
    "Casey Ortiz (Moderate)": CASEY_ORTIZ,
    "Jordan Hale (Aggressive)": JORDAN_HALE,
    "Riley Chen (Aggressive)": RILEY_CHEN,
}

# Drifted mix for the sample so rebalance is visible.
JORDAN_HALE_CURRENT = Mix(stocks_pct=92, bonds_pct=5, cash_pct=3)


REBALANCE_BAND_PCT = 5.0  # auto-rebalance if any sleeve drifts this far


@dataclass
class PaperAccount:
    """Fictional funded account. Dollars, not advice."""

    stocks_usd: float
    bonds_usd: float
    cash_usd: float

    @property
    def value(self) -> float:
        return self.stocks_usd + self.bonds_usd + self.cash_usd

    def as_mix(self) -> Mix:
        v = self.value
        if v <= 0:
            return Mix(0, 0, 0)
        s = int(round(100 * self.stocks_usd / v))
        b = int(round(100 * self.bonds_usd / v))
        c = 100 - s - b
        return Mix(s, b, c)


def open_paper_account(mix: Mix, value: float = DEMO_VALUE) -> PaperAccount:
    return PaperAccount(
        stocks_usd=value * mix.stocks_pct / 100.0,
        bonds_usd=value * mix.bonds_pct / 100.0,
        cash_usd=value * mix.cash_pct / 100.0,
    )


def apply_returns(account: PaperAccount, stock_r: float, bond_r: float, cash_r: float = 0.0) -> PaperAccount:
    return PaperAccount(
        stocks_usd=account.stocks_usd * (1 + stock_r),
        bonds_usd=account.bonds_usd * (1 + bond_r),
        cash_usd=account.cash_usd * (1 + cash_r),
    )


def max_drift_pct(account: PaperAccount, target: Mix) -> float:
    current = account.as_mix()
    return float(
        max(
            abs(current.stocks_pct - target.stocks_pct),
            abs(current.bonds_pct - target.bonds_pct),
            abs(current.cash_pct - target.cash_pct),
        )
    )


def needs_rebalance(account: PaperAccount, target: Mix, band: float = REBALANCE_BAND_PCT) -> bool:
    return max_drift_pct(account, target) >= band


def auto_rebalance(account: PaperAccount, target: Mix) -> PaperAccount:
    v = account.value
    return open_paper_account(target, v)
