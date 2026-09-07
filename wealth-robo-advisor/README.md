# wealth-robo-advisor

Fictional Streamlit robo-advisor for recruiters. Questionnaire → automatic model mix → $100k paper account → simulate / shock → auto-rebalance.

**Portfolio sample only.** Nobody logs in. No real account. No trades. Not investment advice. Not an offer. Not affiliated with Merrill, Bank of America, or any employer.

## Why this is here

Shows an advisor-built demo of rule-based sleeve assignment, drift, and rebalance — plain Python, documented scoring, human-readable UI. Recruiters can run it locally in minutes.

## Demo flow

1. Hypothetical goal, horizon, liquidity, risk tolerance
2. Point system assigns Conservative / Moderate / Aggressive
3. Funds a fictional **$100,000** paper account at the target mix
4. **Simulate one month** (random) or **Apply equity selloff** (canned)
5. **Auto-rebalance** when any sleeve drifts **5 percentage points** from target
6. Stress table on the *target* mix (illustrative math)

See [`examples.md`](examples.md) for the Jordan Hale walkthrough.

## Classification rules

Max score **7**. Not a suitability determination.

| Input | Points |
| --- | --- |
| Horizon: under 5 / 5–10 / 10–20 / 20+ years | 0 / 1 / 2 / 3 |
| Tolerance: low / medium / high | 0 / 1 / 2 |
| Liquidity: cash need <2 / 2–5 / 5+ years | 0 / 1 / 2 |

| Score | Sleeve | Model mix (stocks / bonds / cash) |
| --- | --- | --- |
| 0–2 | Conservative | 30 / 60 / 10 |
| 3–4 | Moderate | 60 / 35 / 5 |
| 5–7 | Aggressive | 85 / 10 / 5 |

## Run it

```bash
cd ~/Codes/AI-Wealth-Management-Projects/wealth-robo-advisor
source .venv/bin/activate
pip install -r requirements.txt   # first time
streamlit run app.py
```

Click a **Sample:** button (Avery / Casey / Jordan / Riley), check the live score, then **Open paper account**.

## Layout

| Path | Role |
| --- | --- |
| `app.py` | Streamlit UI |
| `engine.py` | Scoring, paper account, rebalance, stress |
| `data/model_portfolios.csv` | Sleeve mixes |
| `examples.md` | Sample walkthrough |

## Compliance

- Fictional names and paper dollars only
- Not a client product and not investment advice
- SEC investor bulletin on [robo-advisers](https://www.sec.gov/investor/alerts/robo-advisers.htm)
