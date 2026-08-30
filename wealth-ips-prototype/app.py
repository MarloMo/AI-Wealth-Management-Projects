"""Streamlit demo. Final IPS is hidden until a human clicks Approve."""

from __future__ import annotations

import streamlit as st

from engine import (
    HORIZON_POINTS,
    JORDAN_HALE,
    LIQUIDITY_POINTS,
    TOLERANCE_POINTS,
    InvestorInput,
    approved_packet,
    build_draft,
    load_allocations,
)

DISCLAIMER = (
    "FICTIONAL DEMO. Not investment advice. Not a recommendation. "
    "Not a client product. Hypothetical data only. "
    "A human must click Approve before the final IPS packet is shown."
)

st.set_page_config(page_title="Wealth IPS Prototype", layout="centered")
st.title("Wealth IPS Prototype")
st.caption("Hypothetical advisor workstation — recruiter sample, not a live tool.")
st.warning(DISCLAIMER)

if "approved" not in st.session_state:
    st.session_state.approved = False
if "draft" not in st.session_state:
    st.session_state.draft = None

if st.button("Load sample: Jordan Hale (fictional)"):
    st.session_state.approved = False
    st.session_state.prefill = True

prefill = st.session_state.get("prefill", False)
sample = JORDAN_HALE if prefill else None

st.subheader("1. Hypothetical investor")
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

if st.button("Build draft", type="primary"):
    if not name.strip() or not goal.strip():
        st.error("Enter a fictional name and a goal.")
    else:
        inp = InvestorInput(
            name=name.strip(),
            goal=goal.strip(),
            horizon=horizon,
            liquidity=liquidity,
            tolerance=tolerance,
        )
        st.session_state.draft = build_draft(inp)
        st.session_state.approved = False

draft = st.session_state.draft
if draft is None:
    st.info("Fill in a fictional investor and click Build draft.")
    st.stop()

st.subheader("2. Draft (not final)")
st.write(f"**Proposed category:** {draft.category}")
st.write(draft.score_breakdown)
st.write("**Proposed model allocation**")
st.dataframe(
    load_allocations().loc[[draft.category], ["stocks_pct", "bonds_pct", "cash_pct"]],
    hide_index=False,
)
st.bar_chart(
    {
        "Stocks": draft.stocks_pct,
        "Bonds": draft.bonds_pct,
        "Cash": draft.cash_pct,
    }
)

st.subheader("3. Human approval")
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Approve"):
        st.session_state.approved = True
with col_b:
    if st.button("Reject"):
        st.session_state.approved = False
        st.session_state.draft = None
        st.rerun()

st.subheader("4. Final IPS packet")
if st.session_state.approved:
    st.success("Approved in this demo session. Still not investment advice.")
    st.code(approved_packet(draft), language="text")
else:
    st.error("Final packet is locked until a human clicks Approve.")
    with st.expander("Preview draft text (not the final packet)"):
        st.code(draft.ips_text, language="text")
