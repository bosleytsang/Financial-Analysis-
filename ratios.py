"""
ratios.py

Basel III capital adequacy and liquidity ratio calculations.

All functions take raw dollar-amount inputs (as reported in filings, in the
same units -- typically USD millions or thousands, just stay consistent) and
return a ratio as a decimal (e.g. 0.118 for 11.8%).

Regulatory minimums (standardized approach, well-capitalized thresholds
under Basel III as implemented in the U.S.) are provided as module-level
constants for benchmarking.
"""

from dataclasses import dataclass

# --- Regulatory minimums (Basel III, U.S. implementation) --------------

CET1_MINIMUM = 0.045          # 4.5%
CET1_MINIMUM_WITH_BUFFER = 0.070   # 4.5% + 2.5% capital conservation buffer
TIER1_MINIMUM = 0.060         # 6.0%
TOTAL_CAPITAL_MINIMUM = 0.080  # 8.0%
LEVERAGE_MINIMUM = 0.040      # 4.0%
WELL_CAPITALIZED_LEVERAGE = 0.050  # 5.0% (well-capitalized threshold, insured banks)


@dataclass
class CapitalPosition:
    """Raw balance-sheet / regulatory-capital inputs for one filing period."""
    cet1_capital: float
    tier1_capital: float
    total_capital: float
    risk_weighted_assets: float
    total_assets: float          # for leverage ratio denominator (avg total assets)
    cash_and_equivalents: float
    total_deposits: float
    total_loans: float
    afs_securities: float
    htm_securities: float


def cet1_ratio(cp: CapitalPosition) -> float:
    """Common Equity Tier 1 capital / Risk-Weighted Assets."""
    return cp.cet1_capital / cp.risk_weighted_assets


def tier1_ratio(cp: CapitalPosition) -> float:
    """Tier 1 capital / Risk-Weighted Assets."""
    return cp.tier1_capital / cp.risk_weighted_assets


def total_capital_ratio(cp: CapitalPosition) -> float:
    """Total capital (Tier 1 + Tier 2) / Risk-Weighted Assets."""
    return cp.total_capital / cp.risk_weighted_assets


def leverage_ratio(cp: CapitalPosition) -> float:
    """Tier 1 capital / Average total consolidated assets (non-risk-weighted)."""
    return cp.tier1_capital / cp.total_assets


def loan_to_deposit_ratio(cp: CapitalPosition) -> float:
    """Total loans / Total deposits -- a core funding-mix liquidity indicator."""
    return cp.total_loans / cp.total_deposits


def cash_to_assets_ratio(cp: CapitalPosition) -> float:
    """Cash & equivalents / Total assets -- a simple on-hand liquidity buffer."""
    return cp.cash_and_equivalents / cp.total_assets


def securities_portfolio_mix(cp: CapitalPosition) -> dict:
    """
    Share of investment securities held as AFS vs HTM.
    Elevated HTM share is the specific structural feature that concentrated
    unrealized-loss risk outside of regulatory capital during 2022-2023.
    """
    total = cp.afs_securities + cp.htm_securities
    if total == 0:
        return {"afs_share": None, "htm_share": None}
    return {
        "afs_share": cp.afs_securities / total,
        "htm_share": cp.htm_securities / total,
    }


def summarize(cp: CapitalPosition) -> dict:
    """Return every ratio for one period as a flat dict -- convenient for
    building a multi-period DataFrame with pandas."""
    mix = securities_portfolio_mix(cp)
    return {
        "cet1_ratio": cet1_ratio(cp),
        "tier1_ratio": tier1_ratio(cp),
        "total_capital_ratio": total_capital_ratio(cp),
        "leverage_ratio": leverage_ratio(cp),
        "loan_to_deposit": loan_to_deposit_ratio(cp),
        "cash_to_assets": cash_to_assets_ratio(cp),
        "afs_share_of_securities": mix["afs_share"],
        "htm_share_of_securities": mix["htm_share"],
    }
