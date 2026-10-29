"""Seeded demonstration inputs and strict, fail-fast validation."""
from pathlib import Path
import numpy as np
import pandas as pd
from .cashflows import step, project, risk_measures


def generate(root, seed=42):
    root = Path(root)
    raw = root / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2019-12-31", "2025-12-31", freq="ME")
    # Macro path is generated, never represented as observations from FRED.
    n = len(dates)
    unemployment = 5 + 1.5*np.sin(np.arange(n)/9) + rng.normal(0,.15,n)
    rates = .025 + .012*np.sin(np.arange(n)/13) + rng.normal(0,.001,n)
    macro = pd.DataFrame({"date":dates, "unemployment":unemployment, "base_rate":rates})
    securities, rows, pools = [], [], []
    for d in range(12):
        deal = f"DEAL{d+1:02d}"
        sector = ["Auto", "Equipment", "Consumer"][d % 3]
        initial = float(80_000_000 + d*5_000_000)
        notes = np.array([initial*.8, initial*.2])
        coupons = np.array([.045 + d*.0003, .075 + d*.0003])
        for i, tr in enumerate(["A", "B"]):
            securities.append({"security_id":f"{deal}-{tr}", "deal_id":deal, "sector":sector,
                               "tranche":tr, "rating":"AAA" if i == 0 else "BBB",
                               "coupon":coupons[i], "initial_balance":notes[i], "term_months":120})
        for t, date in enumerate(dates):
            cpr = float(np.clip(.08 + .012*np.cos(t/8+d) + rng.normal(0,.004), .01,.25))
            cdr = float(np.clip(.012 + .004*(unemployment[t]-5) + d*.0002 + rng.normal(0,.001),.001,.08))
            flow = None
            if t:
                flow = step(notes.sum(), notes, coupons, 121-t, cpr, cdr)
                notes = flow["ending_notes"]
            # Price after this month's cash distribution; constant-assumption projected flows.
            future = project(notes, coupons, 120-t, cpr, cdr)
            pools.append({"date":date, "deal_id":deal, "cpr":cpr,"cdr":cdr,
                          "asset_balance":notes.sum(),"unemployment":unemployment[t]})
            for i, tr in enumerate(["A", "B"]):
                sub = future[future.tranche == tr]
                spread = (.009 if i == 0 else .035) + .001*(unemployment[t]-5) + d*.00015
                y = float(rates[t] + spread)
                m = risk_measures((sub.interest+sub.principal).values, sub.principal.values, y)
                rows.append({"date":date,"security_id":f"{deal}-{tr}", "balance":notes[i],
                             "market_value":m.pop("pv"),"yield":y,"spread":spread,
                             "interest":0. if flow is None else flow["interest"][i],
                             "principal":0. if flow is None else flow["principal"][i],
                             "loss":0. if flow is None else flow["loss"][i],
                             "shortfall":0. if flow is None else flow["shortfall"][i], **m})
    sec, panel, pool = pd.DataFrame(securities), pd.DataFrame(rows), pd.DataFrame(pools)
    # One extra exact duplicate tests deterministic cleaning, never modelling signal.
    dirty = pd.concat([panel,panel.iloc[[15]]],ignore_index=True)
    for name, df in {"securities":sec,"monthly_performance":dirty,"pool_performance":pool,"macro":macro}.items():
        df.to_csv(raw/f"{name}.csv",index=False,float_format="%.10f")


def clean(root):
    root = Path(root)
    sec = pd.read_csv(root/"data/raw/securities.csv")
    panel = pd.read_csv(root/"data/raw/monthly_performance.csv",parse_dates=["date"])
    pool = pd.read_csv(root/"data/raw/pool_performance.csv",parse_dates=["date"])
    macro = pd.read_csv(root/"data/raw/macro.csv",parse_dates=["date"])
    before = len(panel)
    panel = panel.drop_duplicates().sort_values(["security_id","date"])
    validate(sec,panel,pool,macro)
    panel["total_return"] = (panel.market_value+panel.interest+panel.principal)/panel.groupby("security_id").market_value.shift()-1
    first = panel.groupby("security_id").cumcount().eq(0)
    if panel.loc[~first,"total_return"].isna().any() or not np.isfinite(panel.loc[~first,"total_return"]).all():
        raise ValueError("Invalid total returns")
    report = {"raw_rows":before,"clean_rows":len(panel),"exact_duplicates_removed":before-len(panel),
              "securities":len(sec),"months":panel.date.nunique(),"seed":42,"data_type":"synthetic"}
    return sec,panel,pool,macro,report


def validate(sec,panel,pool,macro):
    for frame,keys in [(sec,["security_id"]),(panel,["security_id","date"]),(pool,["deal_id","date"]),(macro,["date"])]:
        if frame.isna().any().any() or frame.duplicated(keys).any():
            raise ValueError(f"Nulls or duplicate keys: {keys}")
        nums = frame.select_dtypes(include="number")
        if not np.isfinite(nums.to_numpy()).all():
            raise ValueError("Non-finite source values")
    if not panel.security_id.isin(sec.security_id).all() or not pool.deal_id.isin(sec.deal_id).all():
        raise ValueError("Unknown security or deal")
    dates = sorted(macro.date.unique())
    if list(pd.date_range(min(dates),max(dates),freq="ME")) != dates:
        raise ValueError("Missing macro month")
    if set(pool.deal_id) != set(sec.deal_id):
        raise ValueError("Incomplete pool universe")
    if any(list(g.date.sort_values()) != dates for _,g in panel.groupby("security_id")):
        raise ValueError("Incomplete monthly security panel")
    if set(panel.security_id) != set(sec.security_id) or any(list(g.date.sort_values()) != dates for _,g in pool.groupby("deal_id")):
        raise ValueError("Incomplete universe or pool panel")
    if (panel[["balance","market_value","interest","principal","loss","shortfall"]] < -1e-6).any().any():
        raise ValueError("Negative monetary amount")
    if ((pool[["cpr","cdr"]]<0)|(pool[["cpr","cdr"]]>=1)).any().any():
        raise ValueError("Invalid CPR/CDR")
    reconciled = panel.merge(sec[["security_id","deal_id"]],on="security_id").groupby(["deal_id","date"]).balance.sum()
    expected = pool.set_index(["deal_id","date"]).asset_balance.reindex(reconciled.index)
    if not np.allclose(reconciled,expected,atol=.01,rtol=0):
        raise ValueError("Asset/note balance reconciliation failed")
    for sid,g in panel.sort_values("date").groupby("security_id"):
        initial = sec.set_index("security_id").loc[sid,"initial_balance"]
        previous = g.balance.shift().fillna(initial)
        if not np.allclose(previous-g.principal-g.loss,g.balance,atol=.01,rtol=0):
            raise ValueError("Principal/loss conservation failed")
