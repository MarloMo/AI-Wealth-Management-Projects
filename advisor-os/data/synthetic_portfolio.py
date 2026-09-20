"""Synthetic portfolio holdings for Advisor OS development."""

portfolios = {
    "C001": {
        "client_id": "C001",
        "as_of_date": "2026-09-01",
        "currency": "USD",
        "holdings": [
            {
                "ticker": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "asset_class": "Equity",
                "shares": 1600,
                "cost_basis": 320000,
                "current_value": 400000,
            },
            {
                "ticker": "BND",
                "name": "Vanguard Total Bond Market ETF",
                "asset_class": "Fixed Income",
                "shares": 2800,
                "cost_basis": 205000,
                "current_value": 200000,
            },
            {
                "ticker": "VXUS",
                "name": "Vanguard Total International Stock ETF",
                "asset_class": "Equity",
                "shares": 1900,
                "cost_basis": 110000,
                "current_value": 125000,
            },
            {
                "ticker": "CASH",
                "name": "Cash / Money Market",
                "asset_class": "Cash",
                "shares": 1,
                "cost_basis": 125000,
                "current_value": 125000,
            },
        ],
    },
    "C002": {
        "client_id": "C002",
        "as_of_date": "2026-09-01",
        "currency": "USD",
        "holdings": [
            {
                "ticker": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "asset_class": "Equity",
                "shares": 500,
                "cost_basis": 110000,
                "current_value": 126000,
            },
            {
                "ticker": "BND",
                "name": "Vanguard Total Bond Market ETF",
                "asset_class": "Fixed Income",
                "shares": 2000,
                "cost_basis": 150000,
                "current_value": 147000,
            },
            {
                "ticker": "VXUS",
                "name": "Vanguard Total International Stock ETF",
                "asset_class": "Equity",
                "shares": 1100,
                "cost_basis": 65000,
                "current_value": 71400,
            },
            {
                "ticker": "CASH",
                "name": "Cash / Money Market",
                "asset_class": "Cash",
                "shares": 1,
                "cost_basis": 75600,
                "current_value": 75600,
            },
        ],
    },
}
