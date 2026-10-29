# ABS Performance Analysis — Quantitative Research Lab

A reproducible Python project for **fixed-income analytics, portfolio construction, index research, time-series modelling and dashboard development**. The project follows 12 simulated asset pools and 24 senior/junior notes, models their cash flows and compares allocation strategies against a rules-based ABS index.

**All data and investment results are simulated.** This is a research portfolio project, not a live investment product or a calibrated deal-pricing system.

## Start here

Requires Python 3.10+ (validated on 3.12). From a terminal in the repository:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux instead: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m abs_lab.pipeline
python -m pytest -q
python -m abs_lab.dashboard
```

Open **http://127.0.0.1:8050**. The dashboard uses **Python Dash and Plotly**. No account, API key or database is required for the core workflow. Keep the terminal running while using the dashboard. If Windows blocks activation, invoke `.venv\Scripts\python.exe` directly in place of `python`.

The committed sample CSVs make the analysis reproducible. To regenerate the same raw dataset, run `python -m abs_lab.pipeline --regenerate`; this intentionally overwrites the demo CSVs. Run the pipeline before launching the app if processed outputs are missing. Run `python scripts/execute_notebook.py` to execute the complete notebook without opening Jupyter.

## What is built

| JD requirement | Evidence in this repository |
|---|---|
| Python, pandas, NumPy, data cleansing | `src/abs_lab/data.py`, validation tests, reproducible CSV inputs |
| Fixed income / ABS | Sequential-pay waterfall, junior-first losses, prepayments, recoveries, PV, duration, convexity and WAL in `cashflows.py` |
| Portfolio analytics / asset allocation | Constrained CVXPY minimum-variance allocation, monthly backtesting and benchmark-relative diagnostics |
| Index construction | Prior-month eligibility and market-value weights, monthly rebalancing, total-return index |
| Manager evaluation | Three rule-based portfolios compared with benchmark using tracking error, information ratio and HAC regression; **not real managers** |
| Time series / statistics / machine learning | statsmodels OLS, scikit-learn random forest, persistence baseline and expanding-window forecasts |
| Building dashboards in Python Dash | Sector/seniority/scenario filters, note tables, allocation charts, index performance and ML comparison |
| SQL / RDBMS database design | SQL Server DDL, keys/checks/index, transactional staged upserts and window-function queries; **live server validation pending** |
| Automated reports | Reproducible CSVs, Plotly HTML charts and a plain-English research brief |
| AI-assisted research | Offline evidence prompt plus optional API commentary with typed evidence validation and human review |

## Inspect the work

- [Executed quantitative research notebook](notebooks/01_abs_quantitative_research.ipynb)
- [Plain-English research brief](reports/executive_summary.md)
- [Methodology, index rules and limitations](docs/methodology.md)
- [Data dictionary](docs/data_dictionary.md)
- [SQL Server setup](docs/sql_server.md)
- [Validation record](docs/validation.md)
- [Portfolio performance data](data/processed/manager_evaluation.csv)
- [Forecast comparison](data/processed/model_metrics.csv)

## Repository layout

- `src/abs_lab/`: reusable Python modules and CLI entry points.
- `notebooks/`: executed analysis with assumptions, calculations and interpretation.
- `data/raw/`: security master, monthly performance, collateral and macro inputs.
- `data/processed/`: validated data, holdings, backtests, stress and ML results.
- `sql/`: Microsoft SQL Server schema and analytical queries.
- `reports/`: generated report, evidence facts and interactive HTML charts.
- `tests/`: cash conservation, input corruption, no-look-ahead, constraints and Dash callback tests.
- `.github/workflows/ci.yml`: automated pipeline, tests and notebook execution.

## Research choices

December 2019–December 2025 snapshots; 24-month rolling allocation window; January 2022–December 2025 out-of-sample backtest. Strategies pay 10bp per unit of one-way turnover. The index is gross of costs. ML predicts next month's mean annual CDR, independently of portfolio allocation.

This is a **securitized-credit allocation** project, not a complete equity/bond multi-asset optimizer. The fixed cohort, simplified amortization and synthetic macro relationships intentionally limit market realism. See the methodology before quoting results. A successful notebook or dashboard does not establish two years of professional SQL Server or quantitative-development experience.

## Optional AI commentary

```bash
python -m abs_lab.ai_brief
```

This only creates `reports/ai_prompt.txt`. For a live call, set `OPENAI_API_KEY` and `ABS_AI_MODEL` to a compatible Chat Completions model and run `python -m abs_lab.ai_brief --call-api`. It sends the small simulated aggregate evidence packet, may incur API charges and writes a **REVIEW_REQUIRED** result. No live AI call was made during validation.

## Reproduce the environment

`pyproject.toml` defines compatible dependency ranges. `requirements-lock.txt` captures the exact resolved research dependencies used for this build. For a pinned install: `python -m pip install -r requirements-lock.txt` followed by `python -m pip install -e . --no-deps`.
