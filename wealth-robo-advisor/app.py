"""Fictional robo-advisor demo. Paper money only. Not an offer."""

from __future__ import annotations

import random

import pandas as pd
import streamlit as st

from engine import (
    DEMO_VALUE,
    HORIZON_POINTS,
    LIQUIDITY_POINTS,
    REBALANCE_BAND_PCT,
    SAMPLE_CLIENTS,
    STRESS_SCENARIOS,
    TOLERANCE_POINTS,
    InvestorInput,
    Mix,
    apply_returns,
    auto_rebalance,
    build_draft,
    category_from_score,
    max_drift_pct,
    needs_rebalance,
    open_paper_account,
    rebalance_trades,
    stress_table,
)

DISCLAIMER = (
    "FICTIONAL ROBO-ADVISOR SIMULATION. Paper money only. "
    "Not an offer. Not investment advice. Not a client product. "
    "No real account is opened and no trades are sent."
)

st.set_page_config(page_title="Fictional Robo-Advisor", layout="centered")
st.title("Fictional robo-advisor")
st.caption("Questionnaire → automatic mix → paper account → auto-rebalance. Recruiter demo.")
st.warning(DISCLAIMER)

if "account" not in st.session_state:
    st.session_state.account = None
if "draft" not in st.session_state:
    st.session_state.draft = None
if "auto_rebalance_notice" not in st.session_state:
    st.session_state.auto_rebalance_notice = None
if "value_history" not in st.session_state:
    st.session_state.value_history = []
if "sim_month" not in st.session_state:
    st.session_state.sim_month = 0


def record_value(value: float, label: str, detail: str = "") -> None:
    """Append a labeled point for the paper-value chart and history table."""
    st.session_state.value_history.append(
        {
            "month": int(st.session_state.sim_month),
            "seq": len(st.session_state.value_history),
            "event": label,
            "detail": detail or label,
            "paper_value": round(float(value), 2),
        }
    )


def target_mix() -> Mix:
    d = st.session_state.draft
    return Mix(d.stocks_pct, d.bonds_pct, d.cash_pct)




if st.session_state.account is None:
    st.subheader("Open a demo account")
    st.caption("Pick a fictional sample to compare scores, or fill the form yourself.")

    cols = st.columns(2)
    labels = list(SAMPLE_CLIENTS.keys())
    for i, label in enumerate(labels):
        with cols[i % 2]:
            if st.button(f"Sample: {label}", key=f"sample_{i}"):
                st.session_state.sample_key = label
                st.rerun()

    sample_key = st.session_state.get("sample_key")
    sample = SAMPLE_CLIENTS.get(sample_key) if sample_key else None

    name = st.text_input("Name (fictional)", value=sample.name if sample else "")
    goal = st.text_input("Goal", value=sample.goal if sample else "")
    horizon = st.selectbox(
        "Time horizon",
        list(HORIZON_POINTS),
        index=list(HORIZON_POINTS).index(sample.horizon) if sample else 0,
    )
    liquidity = st.selectbox(
        "Liquidity needs",
        list(LIQUIDITY_POINTS),
        index=list(LIQUIDITY_POINTS).index(sample.liquidity) if sample else 0,
    )
    tolerance = st.selectbox(
        "Risk tolerance",
        list(TOLERANCE_POINTS),
        index=list(TOLERANCE_POINTS).index(sample.tolerance) if sample else 0,
    )

    # Live score from the same fixed rubric as the engine.
    h_pts = HORIZON_POINTS[horizon]
    r_pts = TOLERANCE_POINTS[tolerance]
    l_pts = LIQUIDITY_POINTS[liquidity]
    live_total = h_pts + r_pts + l_pts
    live_category = category_from_score(live_total)
    st.info(
        f"**Live score:** {h_pts} (horizon) + {r_pts} (risk) + {l_pts} (liquidity) "
        f"= **{live_total} / 7** → **{live_category}**"
    )

    if st.button("Open paper account", type="primary"):
        if not name.strip() or not goal.strip():
            st.error("Enter a fictional name and a goal.")
        else:
            inp = InvestorInput(name.strip(), goal.strip(), horizon, liquidity, tolerance)
            draft = build_draft(inp)
            mix = Mix(draft.stocks_pct, draft.bonds_pct, draft.cash_pct)
            st.session_state.draft = draft
            st.session_state.account = open_paper_account(mix, DEMO_VALUE)
            st.session_state.value_history = []
            st.session_state.sim_month = 0
            record_value(
                DEMO_VALUE,
                "Opened",
                f"Opened paper account for {inp.name} with ${DEMO_VALUE:,.0f}. "
                f"Robo assigned {draft.category}: {mix.stocks_pct}/{mix.bonds_pct}/{mix.cash_pct}.",
            )
            st.rerun()
    st.stop()

draft = st.session_state.draft
account = st.session_state.account
tgt = target_mix()


def maybe_auto_rebalance(acct, target, reason: str):
    """When max drift hits the band, reset to target at current paper value."""
    if not needs_rebalance(acct, target):
        return acct, False
    before = acct.value
    before_mix = acct.as_mix()
    reset = auto_rebalance(acct, target)
    after_mix = reset.as_mix()
    msg = (
        f"Auto-rebalance triggered ({reason}). "
        f"Max drift hit the {REBALANCE_BAND_PCT:.0f} pp band. "
        f"Mix moved from {before_mix.stocks_pct}/{before_mix.bonds_pct}/{before_mix.cash_pct} "
        f"to {after_mix.stocks_pct}/{after_mix.bonds_pct}/{after_mix.cash_pct} "
        f"at paper value ${before:,.0f}."
    )
    st.session_state.auto_rebalance_notice = msg
    st.session_state._pending_auto_detail = msg
    return reset, True


# Rebalance before rendering so a past-band session does not flash a drifted mix.
account, did = maybe_auto_rebalance(account, tgt, "drift already past band")
if did:
    st.session_state.account = account
    detail = st.session_state.pop("_pending_auto_detail", "Auto-rebalance")
    if not st.session_state.value_history:
        record_value(account.value, "Opened", "Paper account already open.")
    record_value(account.value, "Auto-rebalance", detail)
    st.rerun()

# Seed history for accounts opened before value tracking existed.
if not st.session_state.value_history:
    record_value(account.value, "Start", "Starting paper value.")

current = account.as_mix()
drift = max_drift_pct(account, tgt)
trades = rebalance_trades(current, tgt, account.value)
stress = stress_table(tgt, account.value)

st.subheader("Paper account")
st.write(f"**Assigned sleeve:** {draft.category}")
st.write(draft.explanation)
m1, m2, m3 = st.columns(3)
m1.metric("Paper value", f"${account.value:,.0f}")
m2.metric("Max drift vs target", f"{drift:.0f} pp")
m3.metric("Rebalance band", f"{REBALANCE_BAND_PCT:.0f} pp")

notice = st.session_state.get("auto_rebalance_notice")
if notice:
    st.success(notice)
    if st.button("Dismiss auto-rebalance notice"):
        st.session_state.auto_rebalance_notice = None
        st.rerun()

# Actions first so simulate / selloff / rebalance are one scroll away.
st.subheader("Robo actions")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Simulate one month"):
        stock_r = random.uniform(-0.04, 0.05)
        bond_r = random.uniform(-0.015, 0.015)
        updated = apply_returns(account, stock_r, bond_r, 0.001)
        st.session_state.sim_month = int(st.session_state.sim_month) + 1
        sim_detail = (
            f"Month {st.session_state.sim_month}: "
            f"stocks {stock_r:+.1%}, bonds {bond_r:+.1%}."
        )
        record_value(updated.value, "Simulated month", sim_detail)
        updated, did = maybe_auto_rebalance(updated, tgt, "after simulated month")
        if did:
            detail = st.session_state.pop("_pending_auto_detail", "Auto-rebalance")
            record_value(updated.value, "Auto-rebalance", detail)
        st.session_state.account = updated
        st.rerun()
with c2:
    if st.button("Apply equity selloff"):
        s = STRESS_SCENARIOS["Equity selloff"]
        updated = apply_returns(account, s["stocks"], s["bonds"], s["cash"])
        record_value(
            updated.value,
            "Equity selloff",
            "Applied canned equity selloff shock (stocks −20%, bonds +2%).",
        )
        updated, did = maybe_auto_rebalance(updated, tgt, "after equity selloff")
        if did:
            detail = st.session_state.pop("_pending_auto_detail", "Auto-rebalance")
            record_value(updated.value, "Auto-rebalance", detail)
        st.session_state.account = updated
        st.rerun()
with c3:
    # Manual override: force rebalance even inside the band.
    if st.button("Rebalance now", type="primary"):
        before = account.value
        before_mix = account.as_mix()
        reset = auto_rebalance(account, tgt)
        after_mix = reset.as_mix()
        st.session_state.account = reset
        msg = (
            f"Manual rebalance applied. "
            f"Mix moved from {before_mix.stocks_pct}/{before_mix.bonds_pct}/{before_mix.cash_pct} "
            f"to {after_mix.stocks_pct}/{after_mix.bonds_pct}/{after_mix.cash_pct} "
            f"at paper value ${before:,.0f}."
        )
        st.session_state.auto_rebalance_notice = msg
        record_value(reset.value, "Manual rebalance", msg)
        st.rerun()

st.caption(
    f"When any sleeve drifts {REBALANCE_BAND_PCT:.0f}+ pp from target, the robo "
    "rebalances automatically. **Rebalance now** forces a reset anytime."
)

st.write("**Holdings vs target**")
st.dataframe(trades, hide_index=True)

st.subheader("Paper portfolio value over time")
hist = st.session_state.value_history
if len(hist) >= 1:
    hist_df = pd.DataFrame(hist)
    # Steps stay in months; chart x-axis is years (month / 12), including fractions.
    chron = hist_df.sort_values("seq").copy()
    chron["Year"] = chron["month"] / 12.0
    chart_df = chron[["Year", "paper_value"]].rename(
        columns={"paper_value": "Paper value ($)"}
    )
    st.line_chart(
        chart_df,
        x="Year",
        y="Paper value ($)",
        x_label="Year",
        y_label="Paper portfolio value ($)",
    )
    st.caption(
        "Actions advance in months; the chart shows years (12 months = 1.0). "
        "Month 0 / Year 0 is account open. Selloff and rebalance stay in the current month. "
        "Fictional paper dollars only."
    )
    with st.expander("Activity and value history"):
        table_df = hist_df.sort_values("seq", ascending=False).copy()
        table_df["Year"] = (table_df["month"] / 12.0).round(3)
        table_df = table_df.rename(
            columns={
                "month": "Month",
                "event": "Event",
                "detail": "Detail",
                "paper_value": "Paper value ($)",
            }
        )[["Month", "Year", "Event", "Detail", "Paper value ($)"]]
        st.dataframe(table_df, hide_index=True)
else:
    st.caption("Value history will appear after the paper account is opened.")

st.subheader("Stress on the target mix")
# Compact scenario metrics instead of a chart that repeats the table.
scols = st.columns(len(stress))
for col, row in zip(scols, stress.itertuples(index=False)):
    col.metric(row.scenario, f"{row.est_change_pct:+.1f}%", f"${row.est_value:,.0f} paper")
st.dataframe(stress, hide_index=True)
st.caption("Canned shocks on the *target* mix. Illustrative paper math only — not a forecast.")


if st.button("Close demo account"):
    st.session_state.account = None
    st.session_state.draft = None
    st.session_state.sample_key = None
    st.session_state.auto_rebalance_notice = None
    st.session_state.value_history = []
    st.session_state.sim_month = 0
    st.rerun()
