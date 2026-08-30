# wealth-ips-prototype

Hypothetical advisor prototype: risk intake, model allocation, IPS draft, human approval. Fictional data only. Not a client product. Not investment advice.

This repository is a **portfolio sample** for recruiters evaluating an advisor who can apply AI/software to wealth-management work. Nobody logs in. There is no client data. It does not place trades and it does not make a recommendation.

## What v1 does

1. Collects a *hypothetical* investor’s goal, time horizon, liquidity needs, and risk tolerance.
2. Classifies that profile into Conservative / Moderate / Aggressive with a **documented point system** (not a black-box model).
3. Maps the category to a model mix in `data/model_portfolios.csv`.
4. Drafts a short investment-policy summary.
5. Hides the final packet until a human clicks **Approve**.

Rebalancing, market-stress tests, and PyPortfolioOpt are **not** in v1.

## Classification rules (transparent)

Each answer adds points. Max score is 7.

| Input | Points |
| --- | --- |
| Horizon: under 5 / 5–10 / 10–20 / 20+ years | 0 / 1 / 2 / 3 |
| Tolerance: low / medium / high | 0 / 1 / 2 |
| Liquidity: cash <2 years / 2–5 years / 5+ years | 0 / 1 / 2 |

- 0–2 Conservative  
- 3–4 Moderate  
- 5–7 Aggressive  

This is a demo mapping, **not** a suitability determination.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Click **Load sample: Jordan Hale (fictional)** to demo in 30 seconds.

## Stack

- Python
- Streamlit
- pandas
- CSV model portfolios

## Compliance

- Fictional names and goals only.
- Not investment advice, not a recommendation, not an offer.
- Not affiliated with Merrill, Bank of America, or any employer.
- A human reviewer must approve before the final packet is shown.
- See the SEC investor bulletin on [robo-advisers](https://www.sec.gov/investor/alerts/robo-advisers.htm) for why disclosures and human oversight matter.

## v2 (not built)

- Rebalancing illustration
- Market-stress scenarios
- Optional PyPortfolioOpt math, still with human approval
