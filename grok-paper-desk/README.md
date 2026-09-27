# grok-paper-desk

Paper-trading research harness: Grok manages a simulated portfolio with **no brokerage connection**. Prices from yfinance. Ledger in local SQLite. Decisions via the xAI API.

**Not a client product. Not investment advice. Not an offer.** Paper money only. Independently developed and not affiliated with Merrill, Bank of America, or any employer.

## Mandate

Beat the S&P 500 (SPY) on a rolling window with `$100,000` virtual cash. Long-only. No shorts, options, or leverage. Hold is valid.

## Layout

| File | Role |
| --- | --- |
| `ledger.py` | SQLite paper ledger: cash, positions, buy/sell/snapshot, audit |
| `market.py` | Prices and SPY return via yfinance |
| `agent.py` | Prompt, xAI call, strict JSON schema validation |
| `desk.py` | Loop: snapshot → decide → validate → execute → log |
| `config.yaml` | Cash, universe, model, schedule, risk caps |
| `.env` | `XAI_API_KEY` only (never commit) |

## Security (v1)

- `EXECUTION_MODE` is hardcoded to **paper**. There is no broker adapter.
- Agent output is untrusted: schema allowlist, ticker checks, share and cash guards.
- Trades mark at `market.get_price`, never at a model-supplied price.
- `.env` is gitignored. Audit rejects are logged with reason codes.

## Setup

```bash
cd ~/Codes/AI-Wealth-Management-Projects/grok-paper-desk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set XAI_API_KEY
chmod 600 .env
```

## Run

```bash
# unit tests (no network / no xAI required for ledger + schema)
pytest -q

# one tick (uses yfinance; uses xAI unless --dry-run)
python desk.py --dry-run
python desk.py

# scheduled ticks during market hours (PT)
python desk.py --loop
```

## Performance tracking

Each tick compares paper **NAV vs starting cash ($100,000)** and **SPY** (benchmark via yfinance) since desk start:

- `desk_return_since_start` = `(NAV / starting_nav) - 1`
- `spx_return_since_start` = SPY total return since desk `started_at` (name kept for audit continuity; SPY-based, not the SPX index)
- `excess_return` = desk return − SPY return

These fields appear on the terminal summary line and on every audit JSONL row in `logs/decisions.jsonl`.

## Disclaimer

Paper performance is not live performance. No slippage, borrow, or tax model is included. This is a research harness, not advice and not a brokerage product.
