"""
stress_test.py

A simplified sensitivity/stress test: what happens to a bank's CET1 ratio
if (a) it experiences a deposit outflow large enough to force asset sales,
and (b) it realizes a markdown on its AFS/HTM securities portfolio.

This is deliberately transparent and simple -- it is NOT a regulatory-grade
model (like the Fed's DFAST/CCAR) -- but it demonstrates the core mechanism
that drove the March 2023 regional bank stress: forced securities sales at
a loss eroding capital.

Mechanism modeled:
1. A deposit outflow of `deposit_outflow_pct` forces the bank to sell
   securities to meet withdrawals.
2. Those securities are sold at a markdown of `securities_markdown_pct`
   (reflecting unrealized losses becoming realized).
3. The realized loss reduces CET1 capital dollar-for-dollar (post-tax
   effect is ignored for simplicity -- see note below).
4. RWA is held constant (a simplification; in practice RWA could fall
   slightly as the balance sheet shrinks).
"""

from dataclasses import replace

from ratios import CapitalPosition, cet1_ratio, CET1_MINIMUM_WITH_BUFFER


def apply_stress(
    cp: CapitalPosition,
    deposit_outflow_pct: float,
    securities_markdown_pct: float,
) -> tuple[CapitalPosition, dict]:
    """
    Apply a deposit-outflow + securities-markdown shock to a CapitalPosition
    and return the stressed position plus a summary of the impact.

    deposit_outflow_pct: e.g. 0.10 for a 10% deposit outflow
    securities_markdown_pct: e.g. 0.05 for a 5% markdown on securities sold
        to fund that outflow (calibrate this using the bank's actual AOCI /
        securities fair-value disclosures for a realistic scenario)
    """
    securities_book = cp.afs_securities + cp.htm_securities
    deposits_withdrawn = cp.total_deposits * deposit_outflow_pct

    # Assume securities sold to cover the outflow (capped at total securities book)
    securities_sold = min(deposits_withdrawn, securities_book)
    realized_loss = securities_sold * securities_markdown_pct

    stressed_cet1_capital = cp.cet1_capital - realized_loss
    stressed_deposits = cp.total_deposits - deposits_withdrawn
    stressed_securities = securities_book - securities_sold

    stressed_cp = replace(
        cp,
        cet1_capital=stressed_cet1_capital,
        tier1_capital=cp.tier1_capital - realized_loss,
        total_capital=cp.total_capital - realized_loss,
        total_deposits=stressed_deposits,
        total_assets=cp.total_assets - securities_sold,
        # split the remaining securities proportionally across AFS/HTM
        afs_securities=stressed_securities * (cp.afs_securities / securities_book) if securities_book else 0,
        htm_securities=stressed_securities * (cp.htm_securities / securities_book) if securities_book else 0,
    )

    baseline_ratio = cet1_ratio(cp)
    stressed_ratio = cet1_ratio(stressed_cp)

    summary = {
        "baseline_cet1_ratio": baseline_ratio,
        "stressed_cet1_ratio": stressed_ratio,
        "cet1_ratio_decline_pp": (baseline_ratio - stressed_ratio) * 100,
        "realized_loss": realized_loss,
        "breaches_buffer_minimum": stressed_ratio < CET1_MINIMUM_WITH_BUFFER,
    }
    return stressed_cp, summary


def run_scenario_grid(
    cp: CapitalPosition,
    outflow_range: list[float],
    markdown_range: list[float],
) -> "pd.DataFrame":
    """
    Run apply_stress across a grid of outflow x markdown assumptions and
    return a tidy DataFrame -- useful for a heatmap of stressed CET1 ratios.
    """
    import pandas as pd

    rows = []
    for outflow in outflow_range:
        for markdown in markdown_range:
            _, summary = apply_stress(cp, outflow, markdown)
            rows.append(
                {
                    "deposit_outflow_pct": outflow,
                    "securities_markdown_pct": markdown,
                    **summary,
                }
            )
    return pd.DataFrame(rows)


# Note on simplifications:
# - Ignores tax effects on realized losses (in reality, losses are partially
#   offset by a tax benefit, reducing the capital hit).
# - Holds RWA constant; a shrinking balance sheet would modestly reduce RWA
#   and partially offset the ratio decline.
# - Assumes securities are sold pro-rata from the existing AFS/HTM mix;
#   in practice AFS securities are far easier to liquidate than HTM.
# These are documented explicitly so the limitations are transparent --
# state them in your writeup rather than presenting the output as precise.
