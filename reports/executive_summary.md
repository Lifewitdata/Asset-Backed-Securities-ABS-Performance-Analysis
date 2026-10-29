# ABS research brief

**Demonstration only: all securities, prices, macro data and results are simulated.**

## Question
How do credit losses, prepayments and interest rates affect a securitized-credit portfolio, and can allocation constraints reduce measured risk?

## Findings from this run
- The dataset contains 24 notes across 12 pools and 73 month-end snapshots. Validation removed 1 exact duplicate; balances reconcile after principal payments and write-downs.
- Over 48 out-of-sample monthly observations, the illustrative ABS index returned 5.48% annualised with 1.41% volatility. The constrained minimum-variance strategy returned 3.80%, with 0.72% volatility after modelled trading costs.
- The most adverse defined scenario changes the full remaining universe's value by $-17,231,791. This is a repricing scenario, not a probability-weighted loss forecast.
- The lowest forecast MAE belongs to **OLS** at 6.78 basis points of annual CDR. Compare all models against persistence; complexity alone is not evidence of value.

## Practical interpretation
Inspect junior-note losses and extension sensitivity before choosing an allocation. Use issuer/deal diversification and client constraints in addition to historical volatility. Do not infer manager skill from the three rule-based demonstration portfolios.

## Limits
Fixed cohort, simplified two-note waterfall, instant recoveries, constant forward prepayment/default assumptions, no taxes or liquidity model. Simulated relationships make both backtests and ML results unsuitable as estimates of real-market performance. SQL Server integration requires a separate configured server. See docs/methodology.md.

## Supporting outputs
- [Portfolio chart](portfolio_performance.html)
- [Scenario chart](stress_scenarios.html)
- Numeric results: data/processed/manager_evaluation.csv and model_metrics.csv.
