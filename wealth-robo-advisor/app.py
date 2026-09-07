"""Fictional robo-advisor demo. Paper money only. Not an offer."""

from __future__ import annotations

import random

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
if "log" not in st.session_state:
    st.session_state.log = []


def log(msg: str) -> None:
    st.session_state.log.insert(0, msg)


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
            st.session_state.log = [
                f"Opened paper account for {inp.name} with ${DEMO_VALUE:,.0f}. "
                f"Robo assigned {draft.category}: {mix.stocks_pct}/{mix.bonds_pct}/{mix.cash_pct}."
            ]
            st.rerun()
    st.stop()

draft = st.session_state.draft
account = st.session_state.account
tgt = target_mix()
current = account.as_mix()
drift = max_drift_pct(account, tgt)
rebalance_due = needs_rebalance(account, tgt)

st.subheader("Paper account")
st.write(f"**Assigned sleeve:** {draft.category}")
st.write(draft.explanation)
m1, m2, m3 = st.columns(3)
m1.metric("Paper value", f"${account.value:,.0f}")
m2.metric("Max drift vs target", f"{drift:.0f} pp")
m3.metric("Rebalance band", f"{REBALANCE_BAND_PCT:.0f} pp")

st.write("**Holdings vs target**")
st.dataframe(
    rebalance_trades(current, tgt, account.value),
    hide_index=True,
)

st.subheader("Robo actions")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Simulate one month"):
        stock_r = random.uniform(-0.04, 0.05)
        bond_r = random.uniform(-0.015, 0.015)
        st.session_state.account = apply_returns(account, stock_r, bond_r, 0.001)
        log(f"Simulated month: stocks {stock_r:+.1%}, bonds {bond_r:+.1%}.")
        st.rerun()
with c2:
    if st.button("Apply equity selloff"):
        s = STRESS_SCENARIOS["Equity selloff"]
        st.session_state.account = apply_returns(account, s["stocks"], s["bonds"], s["cash"])
        log("Applied canned equity selloff shock.")
        st.rerun()
with c3:
    if st.button("Auto-rebalance", type="primary", disabled=not rebalance_due):
        before = account.value
        st.session_state.account = auto_rebalance(account, tgt)
        log(f"Auto-rebalanced to target. Paper value ${before:,.0f}.")
        st.rerun()

if rebalance_due:
    st.info("Drift is at or past the 5 point band. The robo would rebalance. Click Auto-rebalance.")
else:
    st.caption("Drift is inside the band, so the robo holds.")

st.subheader("Stress on the target mix")
st.dataframe(stress_table(tgt, account.value), hide_index=True)

st.subheader("Activity log")
for line in st.session_state.log:
    st.write(f"- {line}")

if st.button("Close demo account"):
    st.session_state.account = None
    st.session_state.draft = None
    st.session_state.log = []
    st.session_state.sample_key = None
    st.rerun()
