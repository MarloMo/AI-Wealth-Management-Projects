# Example run (fictional)

Walkthrough of the Streamlit demo. No real client data. Not investment advice.

## 1. Open the sample account

Click **Use sample: Jordan Hale (fictional)**, then **Open paper account**.

| Field | Sample value | Points |
| --- | --- | --- |
| Name | Jordan Hale (fictional) | — |
| Goal | Retirement income in about 18 years | — |
| Time horizon | 10–20 years | 2 |
| Liquidity | Unlikely to need this money for 5+ years | 2 |
| Risk tolerance | Medium — some ups and downs | 1 |

**Engine result:** score **5 / 7** → **Aggressive** → target mix **85% stocks / 10% bonds / 5% cash**.

The paper account starts at that target mix with fictional **$100,000**.

## 2. Move the account (demo actions)

| Button | What it does |
| --- | --- |
| **Simulate one month** | Applies random paper returns to stocks/bonds (tiny cash yield). |
| **Apply equity selloff** | Applies a canned shock so holdings drift from target. |
| **Auto-rebalance** | Enabled when any sleeve is **5+ percentage points** from target; resets to the assigned mix. |

Activity shows in the on-screen log. **Close demo account** clears session state.

## 3. Illustration: drifted mix → rebalance

If holdings were drifted to **92% / 5% / 3%** vs the Aggressive target **85% / 10% / 5%** on $100,000 paper:

| Sleeve | Action |
| --- | --- |
| Stocks | Sell $7,000 |
| Bonds | Buy $5,000 |
| Cash | Buy $2,000 |

## 4. Stress on the *target* mix (canned math)

Approximate paper P&L on the Aggressive target (not a forecast):

| Scenario | Est. change |
| --- | --- |
| Equity selloff | about −16.8% |
| Rates shock | about −5.0% |
| Inflation scare | about −9.1% |

Still not investment advice. Not an offer. Not a client product.


## Compare fictional samples

Same fixed rubric for every fictional client: **total = horizon + risk + liquidity** (max 7).

| Sample | Horizon | Risk | Liquidity | Score | Sleeve |
| --- | --- | --- | --- | --- | --- |
| Avery Nguyen | Under 5 (0) | Low (0) | Need cash &lt;2y (0) | 0 | Conservative |
| Casey Ortiz | 5–10 (1) | Medium (1) | Might need 2–5y (1) | 3 | Moderate |
| Jordan Hale | 10–20 (2) | Medium (1) | Unlikely 5+y (2) | 5 | Aggressive |
| Riley Chen | 20+ (3) | High (2) | Unlikely 5+y (2) | 7 | Aggressive |

In the app, use the **Sample:** buttons, watch the live score line, then **Open paper account**.
