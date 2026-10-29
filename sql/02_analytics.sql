-- Recompute total return without look-ahead. Month zero has no return.
WITH Valuations AS (
 SELECT *, LAG(market_value) OVER (PARTITION BY security_id ORDER BY date) AS opening_value
 FROM dbo.MonthlyPerformance
)
SELECT date,security_id,
 (market_value+interest+principal)/NULLIF(opening_value,0)-1 AS total_return
FROM Valuations ORDER BY security_id,date;

-- Sector risk summary, weighted by current market value.
SELECT p.date,s.sector,SUM(p.market_value) AS market_value,
 SUM(p.market_value*p.duration)/NULLIF(SUM(p.market_value),0) AS weighted_duration,
 SUM(p.market_value*p.yield)/NULLIF(SUM(p.market_value),0) AS weighted_yield,
 SUM(p.loss) AS principal_loss
FROM dbo.MonthlyPerformance p JOIN dbo.Security s ON p.security_id=s.security_id
GROUP BY p.date,s.sector ORDER BY p.date,s.sector;

-- Independently check the accounting identity (should return zero rows).
WITH Balances AS (
 SELECT p.*, COALESCE(LAG(p.balance) OVER (PARTITION BY p.security_id ORDER BY p.date),s.initial_balance) AS opening_balance
 FROM dbo.MonthlyPerformance p JOIN dbo.Security s ON s.security_id=p.security_id
)
SELECT * FROM Balances WHERE ABS(opening_balance-principal-loss-balance)>0.01;
