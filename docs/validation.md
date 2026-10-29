# Validation record — 29 October 2026

## Executed successfully

- Seeded end-to-end pipeline: 1,753 raw note-month rows, one exact duplicate removed, 1,752 validated rows, 24 notes, 73 snapshots and 48 backtest months.
- `python -m pytest -q`: **47 tests passed**. Tests cover cash/principal conservation, seniority/loss ordering, discount sensitivity, corrupted inputs, exact dollar reconciliation, portfolio constraints, cost calculations, future-data invariance, forecast target timing, SQL statement construction and AI evidence rejection.
- Dash Flask test-client requests: `/`, `/_dash-layout`, `/_dash-dependencies` and CSS return HTTP 200. All 12 sector/seniority combinations and four portfolio selections were tested. An actual POST to `/_dash-update-component` returns the expected four senior Auto notes.
- All 11 notebook code cells executed in sequence with assertions, tables and four chart outputs saved. Execution used `python scripts/execute_notebook.py --in-process` (IPython), because this host blocks Jupyter's ZMQ kernel sockets. Normal Jupyter execution remains available through the default command and CI.
- Offline AI evidence prompt generated without an API call.

## Checks that found and fixed an issue

A corruption test added $100 to a large note balance. NumPy's default relative tolerance initially accepted that error. Reconciliation now uses `rtol=0` and `atol=0.01`, and the corruption is rejected. This is why accounting checks need absolute dollar tolerances.

## Not verified here

- Live Microsoft SQL Server DDL, ODBC connectivity and repeated MERGE loads: no SQL Server instance or credentials were available.
- A live OpenAI completion: no API call was made; schema/evidence validation was unit-tested.
- Browser-rendered visual QA: Chromium download was unavailable in this environment. Dashboard layout/callback transport was tested with Flask's test client, not a browser. The app is not deployed or publicly hosted.
- Hosted GitHub Actions results are separate from the local results above.

## Forecast outcomes

The seeded run has 34 forecast observations. OLS MAE is approximately 6.78bp of annual CDR versus 7.10bp for persistence. Persistence RMSE is approximately 8.82bp versus 9.53bp for OLS. The random forest is worse on both metrics. These are simulated-data results, not demonstrated market predictability.
