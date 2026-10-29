# Data dictionary

All data is synthetic. Monthly snapshots are after the month's cash distribution.

| File / grain | Fields | Meaning / units |
|---|---|---|
| securities / one note | security_id, deal_id, sector, tranche, rating | Keys and simulated classification; A senior, B junior |
| securities | coupon, initial_balance, term_months | Annual decimal coupon, dollars, initial maturity in months |
| monthly_performance / note-month | date, security_id | Month-end composite key; raw contains one intentional exact duplicate |
| performance | balance, market_value | Remaining principal and model PV, dollars |
| performance | yield, spread | Annual effective discount yield and additive spread, decimals |
| performance | interest, principal, loss, shortfall | Current month's paid coupon, principal cash, write-down and unpaid coupon, dollars |
| performance | duration, convexity, wal | Fixed-cash-flow yield sensitivity in years, years squared; principal receipt-weighted years |
| performance | total_return | Decimal holding-period return; blank at initial snapshot |
| pool_performance / deal-month | cpr, cdr | Annual prepayment and default probabilities, decimals |
| pool_performance | asset_balance, unemployment | Closing dollars; simulated unemployment in percent (5 means 5%) |
| macro / month | unemployment, base_rate | Percent and decimal annual discount base rate |
| backtest / portfolio-month | decision_date, date | Information cutoff and following return month |
| backtest | gross_return, net_return, turnover, cost | Decimal returns; one-way weight turnover; return deduction |
| backtest | duration, portfolio_yield, wealth | Prior-date weighted exposures; cumulative growth of 100 |
| holdings / portfolio-note-month | weight | Beginning-of-return-month target weight |
| manager_evaluation / strategy | cagr, annual_volatility, max_drawdown, tracking_error | Decimal annual growth/risks and negative peak-to-trough loss |
| manager_evaluation | information_ratio, alpha_annualised, beta, alpha_pvalue_hac | Benchmark-relative diagnostics; raw-return regression, not CAPM |
| scenarios / scenario-note | base_value, scenario_value, pnl | Dollar PVs and their difference |
| predictions / model-target-month | decision_date, target_date, last_training_target_date | Audit trail for time-based validation |
| predictions | actual, predicted | Equal-deal average annual CDR, decimals |
| model_metrics / model | mae, rmse, observations | Errors in decimal annual CDR and evaluation count |

All source numerical columns are checked for nulls and nonfinite values. SQL uses FLOAT for consistency with numerical research; this schema is not an accounting ledger. Production monetary records should use an explicitly agreed precision/rounding policy.
