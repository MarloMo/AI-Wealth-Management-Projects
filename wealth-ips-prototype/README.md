# wealth-ips-prototype

Fictional robo-advisor simulation: questionnaire, automatic model mix, paper account, auto-rebalance. Paper money only. Not a client product. Not investment advice. Not an offer.

This is a **portfolio sample**. Nobody logs in. No real account is opened. No trades are sent.

## What the robo does

1. Collects a hypothetical investor’s goal, time horizon, liquidity needs, and risk tolerance.
2. **Automatically** assigns Conservative / Moderate / Aggressive from a documented point system.
3. Funds a fictional **$100,000 paper account** at the target mix.
4. Lets you simulate a month of returns (random) or apply a canned equity selloff.
5. **Auto-rebalances** when any sleeve drifts 5 percentage points from target.
6. Shows canned market-stress math on the target mix.

## Classification rules

Each answer adds points. Max score is 7.

| Input | Points |
| --- | --- |
| Horizon: under 5 / 5–10 / 10–20 / 20+ years | 0 / 1 / 2 / 3 |
| Tolerance: low / medium / high | 0 / 1 / 2 |
| Liquidity: cash <2 years / 2–5 years / 5+ years | 0 / 1 / 2 |

- 0–2 Conservative
- 3–4 Moderate
- 5–7 Aggressive

Not a suitability determination.

## Run it

```bash
cd ~/Codes/AI-Wealth-Management-Projects/wealth-ips-prototype
source .venv/bin/activate
streamlit run app.py
```

Click **Use sample: Jordan Hale (fictional)**, then **Open paper account**.

## Compliance

- Fictional names and paper dollars only.
- Not affiliated with Merrill, Bank of America, or any employer.
- See the SEC investor bulletin on [robo-advisers](https://www.sec.gov/investor/alerts/robo-advisers.htm).
