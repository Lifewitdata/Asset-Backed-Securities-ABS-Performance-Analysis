-- SQL Server 2019+. Execute in a dedicated, already-created research database.
IF OBJECT_ID('dbo.Security','U') IS NULL
CREATE TABLE dbo.Security (
 security_id VARCHAR(20) NOT NULL PRIMARY KEY,
 deal_id VARCHAR(20) NOT NULL,
 sector VARCHAR(30) NOT NULL,
 tranche CHAR(1) NOT NULL CHECK (tranche IN ('A','B')),
 rating VARCHAR(8) NOT NULL,
 coupon FLOAT NOT NULL CHECK (coupon >= 0),
 initial_balance FLOAT NOT NULL CHECK (initial_balance >= 0),
 term_months INT NOT NULL CHECK (term_months > 0)
);
GO
IF OBJECT_ID('dbo.MonthlyPerformance','U') IS NULL
CREATE TABLE dbo.MonthlyPerformance (
 date DATE NOT NULL,
 security_id VARCHAR(20) NOT NULL REFERENCES dbo.Security(security_id),
 balance FLOAT NOT NULL CHECK (balance >= 0),
 market_value FLOAT NOT NULL CHECK (market_value >= 0),
 yield FLOAT NOT NULL,
 spread FLOAT NOT NULL,
 interest FLOAT NOT NULL CHECK (interest >= 0),
 principal FLOAT NOT NULL CHECK (principal >= 0),
 loss FLOAT NOT NULL CHECK (loss >= 0),
 shortfall FLOAT NOT NULL CHECK (shortfall >= 0),
 duration FLOAT NOT NULL,
 convexity FLOAT NOT NULL,
 wal FLOAT NOT NULL,
 total_return FLOAT NULL,
 CONSTRAINT PK_MonthlyPerformance PRIMARY KEY (security_id,date)
);
GO
IF OBJECT_ID('dbo.Macro','U') IS NULL
CREATE TABLE dbo.Macro (
 date DATE NOT NULL PRIMARY KEY,
 unemployment FLOAT NOT NULL,
 base_rate FLOAT NOT NULL
);
GO
IF OBJECT_ID('dbo.PoolPerformance','U') IS NULL
CREATE TABLE dbo.PoolPerformance (
 date DATE NOT NULL,
 deal_id VARCHAR(20) NOT NULL,
 cpr FLOAT NOT NULL CHECK (cpr >= 0 AND cpr < 1),
 cdr FLOAT NOT NULL CHECK (cdr >= 0 AND cdr < 1),
 asset_balance FLOAT NOT NULL CHECK (asset_balance >= 0),
 unemployment FLOAT NOT NULL,
 CONSTRAINT PK_PoolPerformance PRIMARY KEY (deal_id,date)
);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_Performance_Date' AND object_id=OBJECT_ID('dbo.MonthlyPerformance'))
CREATE INDEX IX_Performance_Date ON dbo.MonthlyPerformance(date)
INCLUDE (market_value,balance,duration,yield,total_return);
