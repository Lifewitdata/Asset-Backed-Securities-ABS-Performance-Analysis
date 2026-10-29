"""Two-note sequential-pay waterfall; dollars, decimal annual rates, monthly steps."""
import numpy as np
import pandas as pd


def monthly_rate(annual):
    if not 0 <= annual < 1:
        raise ValueError("Annual probability must be in [0, 1)")
    return 1 - (1 - annual) ** (1 / 12)


def step(asset, notes, coupons, months_left, cpr, cdr, recovery=0.4, asset_coupon=0.10):
    """Straight-line scheduled amortization; instant recoveries; no delinquency lag.

    Interest pays A then B, principal pays A then B, loss writes down B then A.
    Residual interest belongs to unmodelled equity. Shortfalls are reported, not accrued.
    """
    notes = np.asarray(notes, dtype=float).copy()
    coupons = np.asarray(coupons, dtype=float)
    if asset < 0 or len(notes) != 2 or np.any(notes < 0) or months_left < 1:
        raise ValueError("Invalid balance or remaining term")
    if not np.isclose(notes.sum(), asset, atol=1e-5, rtol=0):
        raise ValueError("Asset and note balances must reconcile")
    if not 0 <= recovery <= 1:
        raise ValueError("Recovery must be between zero and one")
    scheduled = asset / months_left
    default = (asset - scheduled) * monthly_rate(cdr)
    prepaid = (asset - scheduled - default) * monthly_rate(cpr)
    loss = default * (1 - recovery)
    principal_available = scheduled + prepaid + default * recovery
    fees = asset * .002 / 12
    available_interest = max(0., asset * asset_coupon / 12 - fees)
    interest, principal, losses, shortfall = [np.zeros(2) for _ in range(4)]
    for i in range(2):
        due = notes[i] * coupons[i] / 12
        interest[i] = min(available_interest, due)
        shortfall[i] = due - interest[i]
        available_interest -= interest[i]
        principal[i] = min(notes[i], principal_available)
        principal_available -= principal[i]
        notes[i] -= principal[i]
    left = loss
    for i in [1, 0]:
        losses[i] = min(notes[i], left)
        notes[i] -= losses[i]
        left -= losses[i]
    ending = max(0., asset - scheduled - prepaid - default)
    return {"ending_asset": ending, "ending_notes": notes, "interest": interest,
            "principal": principal, "loss": losses, "shortfall": shortfall,
            "scheduled": scheduled, "prepaid": prepaid, "defaulted": default,
            "recoveries": default * recovery, "fees": fees,
            "equity_interest": available_interest}


def project(notes, coupons, months_left, cpr, cdr, recovery=.4):
    notes = np.asarray(notes, dtype=float).copy()
    rows = []
    for m in range(1, months_left + 1):
        flow = step(notes.sum(), notes, coupons, months_left - m + 1, cpr, cdr, recovery)
        for i, tranche in enumerate(["A", "B"]):
            rows.append({"month": m, "tranche": tranche,
                         "interest": flow["interest"][i], "principal": flow["principal"][i],
                         "loss": flow["loss"][i]})
        notes = flow["ending_notes"]
    return pd.DataFrame(rows)


def present_value(cash, annual_yield):
    if annual_yield <= -1:
        raise ValueError("Yield must exceed -100%")
    t = np.arange(1, len(cash) + 1) / 12
    return float(np.sum(np.asarray(cash) / (1 + annual_yield) ** t))


def risk_measures(cash, principal, annual_yield, bump=.0001):
    pv = present_value(cash, annual_yield)
    if pv <= 0:
        return {"pv": 0., "duration": 0., "convexity": 0., "wal": 0.}
    down, up = present_value(cash, annual_yield-bump), present_value(cash, annual_yield+bump)
    principal = np.asarray(principal)
    wal = float(np.dot(np.arange(1, len(principal)+1)/12, principal)/principal.sum()) if principal.sum() else 0.
    return {"pv": pv, "duration": (down-up)/(2*pv*bump),
            "convexity": (down+up-2*pv)/(pv*bump*bump), "wal": wal}
