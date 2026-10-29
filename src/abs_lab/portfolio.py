"""Lagged, monthly-rebalanced research portfolios and benchmark-relative evaluation."""
import numpy as np
import pandas as pd
import cvxpy as cp
import statsmodels.api as sm
from .cashflows import project, present_value


def optimise(history, snapshot, max_weight=.15, duration_limit=4.):
    """Minimum variance with long-only, note/sector concentration and duration limits."""
    cov = history.cov().to_numpy()*12 + np.eye(history.shape[1])*1e-8
    w = cp.Variable(history.shape[1])
    constraints = [w>=0, w<=max_weight, cp.sum(w)==1, snapshot.duration.to_numpy()@w<=duration_limit]
    for sector in snapshot.sector.unique():
        constraints.append((snapshot.sector==sector).to_numpy(dtype=float)@w<=.5)
    prob = cp.Problem(cp.Minimize(cp.quad_form(w,cp.psd_wrap(cov))),constraints)
    prob.solve(solver="CLARABEL")
    if prob.status not in ["optimal","optimal_inaccurate"] or w.value is None:
        raise ValueError(f"Allocation infeasible: {prob.status}")
    result = np.maximum(w.value,0)
    result /= result.sum()
    if result.max()>max_weight+1e-5 or result@snapshot.duration.to_numpy()>duration_limit+1e-5:
        raise ValueError("Solver constraint violation")
    return result


def backtest(sec,panel,lookback=24,cost_bps=10):
    returns = panel.pivot(index="date",columns="security_id",values="total_return").sort_index()
    merged = panel.merge(sec,on="security_id")
    rows, holdings = [], []
    previous = {}
    # First return month is excluded because there is no opening valuation.
    for t in range(lookback+1,len(returns)):
        date, decision = returns.index[t], returns.index[t-1]
        snap = merged[merged.date==decision].set_index("security_id").reindex(returns.columns)
        eligible = (snap.balance>1_000_000)&(snap.rating.isin(["AAA","BBB"]))&(snap.market_value>0)
        ids = snap.index[eligible]
        s = snap.loc[ids]
        hist = returns.loc[:decision,ids].tail(lookback)
        if hist.isna().any().any():
            raise ValueError("Incomplete past return window")
        market = s.market_value.to_numpy()/s.market_value.sum()
        defensive = (s.tranche=="A").to_numpy(dtype=float); defensive /= defensive.sum()
        income = (s.tranche=="B").to_numpy(dtype=float); income /= income.sum()
        allocation = {"ABS Index":market,"Defensive":defensive,"Income":income,
                      "Minimum variance":optimise(hist,s)}
        for name,w in allocation.items():
            full = pd.Series(0.,index=returns.columns); full.loc[ids]=w
            # Previous units are drifted using total returns, with distributions reinvested.
            old = previous.get(name)
            turnover = 1. if old is None else .5*abs(full-old).sum()
            gross = float(full@returns.loc[date])
            cost = 0. if name=="ABS Index" else turnover*cost_bps/10000
            net = gross-cost
            rows.append({"date":date,"decision_date":decision,"portfolio":name,"gross_return":gross,
                         "net_return":net,"turnover":turnover,"cost":cost,
                         "duration":float(w@s.duration),"portfolio_yield":float(w@s["yield"])})
            previous[name] = full*(1+returns.loc[date])/(1+gross)
            for sid in ids:
                holdings.append({"date":date,"decision_date":decision,"portfolio":name,
                                 "security_id":sid,"weight":full[sid]})
    result = pd.DataFrame(rows)
    result["wealth"] = result.groupby("portfolio").net_return.transform(lambda r:(1+r).cumprod()*100)
    return result,pd.DataFrame(holdings)


def evaluate(backtest):
    series = backtest.pivot(index="date",columns="portfolio",values="net_return")
    bench = series["ABS Index"]
    out=[]
    for name,r in series.items():
        active = r-bench
        wealth=(1+r).cumprod()
        peak=wealth.cummax().clip(lower=1.)
        regression=sm.OLS(r,sm.add_constant(bench)).fit(cov_type="HAC",cov_kwds={"maxlags":3})
        te=active.std(ddof=1)*np.sqrt(12)
        out.append({"portfolio":name,"cagr":wealth.iloc[-1]**(12/len(r))-1,
                    "annual_volatility":r.std(ddof=1)*np.sqrt(12),
                    "max_drawdown":(wealth/peak-1).min(),"tracking_error":te,
                    "information_ratio":float(active.mean()*12/te) if te>1e-10 else 0.,
                    "alpha_annualised":0. if name=="ABS Index" else regression.params.iloc[0]*12,"beta":regression.params.iloc[1],
                    "alpha_pvalue_hac":1. if name=="ABS Index" else regression.pvalues.iloc[0]})
    return pd.DataFrame(out)


def stress(sec,panel,pool):
    date=panel.date.max()
    snap=panel[panel.date==date].merge(sec,on="security_id")
    assumptions=pool[pool.date==date].set_index("deal_id")
    rows=[]
    scenarios={"Base":(0.,1.,1.),"Rates +100bp":(.01,1.,1.),
               "Credit stress":(.015,.75,3.),"Fast prepayment":(-.01,2.,1.),
               "Extension":(.01,.5,1.)}
    age=(date.year-2019)*12+date.month-12
    for deal,g in snap.groupby("deal_id"):
        g=g.sort_values("tranche"); a=assumptions.loc[deal]
        for scenario,(shift,prepay,default) in scenarios.items():
            cf=project(g.balance.to_numpy(),g.coupon.to_numpy(),120-age,
                       min(a.cpr*prepay,.95),min(a.cdr*default,.95))
            for _,s in g.iterrows():
                sub=cf[cf.tranche==s.tranche]
                value=present_value(sub.interest+sub.principal,s["yield"]+shift)
                rows.append({"scenario":scenario,"security_id":s.security_id,"tranche":s.tranche,
                             "base_value":s.market_value,"scenario_value":value,
                             "pnl":value-s.market_value})
    return pd.DataFrame(rows)
