# Capital Adequacy & Liquidity Resilience: Zions Bancorporation (ZION)

**A quantitative analysis of a U.S. regional bank's Basel III capital position and liquidity resilience, benchmarked against the dynamics that drove the March 2023 regional banking stress.**

> CET1 capital ratio, Tier 1 leverage ratio, AFS/HTM securities composition, and a parameterized deposit-outflow / securities-markdown stress test — built on data pulled programmatically from SEC EDGAR filings.

![CET1 ratio chart](outputs/charts/cet1_trend.png)

---

## Thesis

Zions Bancorporation is a $90B-asset regional bank in the same peer group (asset size, uninsured deposit reliance, AFS/HTM securities exposure) as the banks that failed in March 2023. Unlike those banks, Zions has since **rebuilt its capital position materially** — CET1 rose from **10.8% (Q1 2025) to 11.8% (Q2 2026)** — while working down the AOCI drag from unrealized securities losses. This project quantifies that trajectory and stress-tests whether Zions' current capital buffer could absorb a repeat of the 2023 shock.

## Key findings (as of Q2 2026 10-Q)

| Metric | Q2 2025 | Q2 2026 | Regulatory minimum* |
|---|---|---|---|
| CET1 capital ratio | 11.0% | **11.8%** | 4.5% (7.0% w/ buffer) |
| Tier 1 risk-based ratio | 11.1% | **11.9%** | 6.0% |
| Total risk-based ratio | 13.4% | **14.0%** | 8.0% |
| Tier 1 leverage ratio | 8.5% | **9.4%** | 4.0% |
| Tangible common equity ratio | 6.2% | **7.4%** | n/a |

*Basel III minimums under the standardized approach; effective thresholds are higher once the 2.5% capital conservation buffer is included.

Data source: Zions Bancorporation Form 10-Q filings, SEC EDGAR (CIK 0000109380).

## What this project does

1. **Pulls data programmatically** from the SEC EDGAR XBRL "company facts" API — no manual copy-paste from filings (`src/edgar_fetch.py`).
2. **Computes regulatory capital and liquidity ratios** from raw XBRL line items using Basel III definitions (`src/ratios.py`).
3. **Visualizes the multi-year trend** against regulatory minimums.
4. **Runs a parameterized stress test** — deposit outflow rate + AFS/HTM markdown — calibrated to the actual March 2023 regional bank stress episode, applied to Zions' current balance sheet (`src/stress_test.py`).
5. Full walkthrough and interpretation in `notebooks/analysis.ipynb`.

## Why Zions

Regional banks between $10B–$200B in assets were repeatedly flagged during the 2023 crisis as the most exposed segment, given their heavier reliance on uninsured deposits relative to large banks. Zions sits squarely in that group, survived the stress period, and — critically — is still public with a clean, continuous XBRL filing history, making it a better subject for reproducible analysis than a failed bank with discontinued reporting.

## Repo structure

```
bank-capital-liquidity-analysis/
├── README.md
├── requirements.txt
├── src/
│   ├── edgar_fetch.py      # pulls XBRL company facts from SEC EDGAR
│   ├── ratios.py           # Basel III capital & liquidity ratio calculations
│   └── stress_test.py      # deposit outflow / securities markdown stress test
├── notebooks/
│   └── analysis.ipynb      # full walkthrough: data -> ratios -> charts -> stress test -> conclusion
├── data/raw/               # cached EDGAR pulls (gitignored by default; see .gitignore)
└── outputs/charts/         # generated chart images
```

## How to run

```bash
git clone https://github.com/<your-username>/bank-capital-liquidity-analysis.git
cd bank-capital-liquidity-analysis
pip install -r requirements.txt
jupyter notebook notebooks/analysis.ipynb
```

`edgar_fetch.py` requires only an internet connection and a descriptive `User-Agent` header (SEC EDGAR API policy) — set this in the script before running. No API key needed.

## Methodology notes

- **CET1 / Tier 1 / Total capital ratios** use risk-weighted assets (RWA) as the denominator, not total assets — the standard Basel III convention.
- **AOCI / AFS-HTM treatment**: the analysis explicitly tracks unrealized losses on securities transferred from AFS to HTM, since this was the specific mechanism that masked capital fragility at several banks in 2023.
- **Stress test** is a sensitivity exercise, not a regulatory-grade model — it estimates the CET1 impact of (a) a specified deposit outflow forcing asset sales and (b) a specified markdown on AFS/HTM securities, using simplified assumptions documented in `src/stress_test.py`.

## Limitations

- Uses standardized-approach RWA as reported by the bank; does not independently recompute risk weights.
- Stress test does not model second-order effects (credit rating downgrades, counterparty actions, funding cost increases).
- Built for educational/portfolio purposes — not investment advice.

## Author

[Your name] — built as part of a finance job search project focused on bank capital adequacy and liquidity risk analysis.
