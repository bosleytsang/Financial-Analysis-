"""
edgar_fetch.py

Pulls XBRL "company facts" data directly from the SEC EDGAR API for a given
company (by CIK), and extracts the specific facts needed for bank capital
adequacy and liquidity analysis.

No API key required. SEC EDGAR only requires a descriptive User-Agent header
identifying the requester (their fair-access policy) -- set EMAIL below.

Zions Bancorporation, National Association CIK: 0000109380
(Find any company's CIK at https://www.sec.gov/cgi-bin/browse-edgar)
"""

import json
import time
from pathlib import Path

import requests

# --- Configuration -----------------------------------------------------

EMAIL = "your_email@example.com"  # SEC requests a real contact in the User-Agent
HEADERS = {"User-Agent": f"bank-capital-liquidity-analysis ({EMAIL})"}

BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# XBRL tags (US-GAAP / regulatory capital taxonomy) we care about for this
# analysis. Not every bank tags every field identically across years --
# inspect the raw JSON if a tag comes back empty.
RELEVANT_TAGS = {
    "cet1_capital": "CommonEquityTier1CapitalToRiskWeightedAssets",
    "rwa": "RiskWeightedAssets",
    "tier1_capital": "TierOneRiskBasedCapitalToRiskWeightedAssets",
    "total_capital_ratio": "TotalCapitalToRiskWeightedAssets",
    "leverage_ratio": "Tier1LeverageRatio",
    "cash_and_equivalents": "CashAndCashEquivalentsAtCarryingValue",
    "total_deposits": "Deposits",
    "total_loans": "LoansAndLeasesReceivableNetReportedAmount",
    "afs_securities": "AvailableForSaleSecuritiesDebtSecurities",
    "htm_securities": "HeldToMaturitySecurities",
    "total_assets": "Assets",
}


def fetch_company_facts(cik: str, use_cache: bool = True) -> dict:
    """
    Fetch the full XBRL company-facts payload for a given CIK.
    CIK must be the 10-digit zero-padded string, e.g. '0000109380'.
    """
    cache_path = DATA_DIR / f"{cik}_companyfacts.json"
    if use_cache and cache_path.exists():
        return json.loads(cache_path.read_text())

    url = BASE_URL.format(cik=cik)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data))
    time.sleep(0.2)  # be polite to SEC's rate limits (10 req/sec max)
    return data


def extract_tag_series(facts: dict, tag: str, unit: str = "USD") -> list[dict]:
    """
    Pull a single US-GAAP tag's reported values across all filed periods.
    Returns a list of dicts: {end: date, val: value, form: '10-Q'/'10-K', fy, fp}
    """
    try:
        entries = facts["facts"]["us-gaap"][tag]["units"][unit]
    except KeyError:
        return []
    # Keep only 10-K / 10-Q filings (drop amended/other forms for simplicity)
    return [e for e in entries if e.get("form") in ("10-K", "10-Q")]


def build_ratio_input_table(cik: str) -> "pd.DataFrame":
    """
    Convenience function: fetches company facts and assembles a tidy
    DataFrame with one row per filing period and one column per metric
    needed by ratios.py.
    """
    import pandas as pd

    facts = fetch_company_facts(cik)
    frames = {}
    for name, tag in RELEVANT_TAGS.items():
        series = extract_tag_series(facts, tag)
        if not series:
            continue
        df = pd.DataFrame(series)[["end", "val", "form", "fy", "fp"]]
        df = df.drop_duplicates(subset="end", keep="last").set_index("end")
        frames[name] = df["val"]

    table = pd.DataFrame(frames).sort_index()
    return table


if __name__ == "__main__":
    ZIONS_CIK = "0000109380"
    table = build_ratio_input_table(ZIONS_CIK)
    print(table.tail(8))
