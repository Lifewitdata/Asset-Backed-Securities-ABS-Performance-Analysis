# SQL Server setup and maintenance

Core research runs from CSVs. This optional adapter uses Microsoft SQL Server, not SQLite or DuckDB.

1. Create an empty, dedicated research database on SQL Server 2019+ (for example `ABSResearch`). Give a dedicated user permission to create tables/indexes and read/write within this database. Do not use a production database.
2. Install Microsoft's ODBC Driver 18 for SQL Server for your OS, then `python -m pip install -e ".[sqlserver]"`.
3. Configure the SQLAlchemy connection URL through `ABS_SQLSERVER_URL`. URL-encode special characters in passwords. Example template (replace placeholders):
   `mssql+pyodbc://USERNAME:PASSWORD@HOST:1433/ABSResearch?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no`
4. Run `python -m abs_lab.pipeline`, then `python -m abs_lab.database`.
5. Run `sql/02_analytics.sql` in SQL Server Management Studio. The reconciliation query should return no rows.

The loader executes `sql/01_schema.sql` in GO-separated batches. It stages each CSV into a unique temporary-named dbo table, runs a keyed MERGE with HOLDLOCK, removes the staging table and checks destination counts, all in one transaction. Re-running the same dataset updates matching rows without duplication. An exception rolls back the transaction. Existing extra rows cause the load to fail; there is no automatic destructive delete or truncate.

Maintenance: run the loader after validated pipeline refreshes, retain input snapshots, review `reports/data_quality.json`, back up the database under your organization's policy and inspect query plans for the date index. The included GitHub workflow validates Python research; it does **not** connect to your server. Concurrent refreshes should be serialized by the scheduler.

**Validation status:** SQL generation is unit-tested. Live DDL execution, ODBC authentication and repeat-load idempotence require your SQL Server instance and were not tested during this build. Neither the README nor the resume should describe this as a deployed SQL Server system before that check.
