import numpy as np
import pytest
from abs_lab.cashflows import step,project,present_value,risk_measures,monthly_rate

@pytest.mark.parametrize("cpr,cdr",[(0,0),(.08,.02),(.5,.4),(.01,.9)])
def test_cash_and_balance_conservation(cpr,cdr):
    s=step(1000,[800,200],[.04,.08],60,cpr,cdr)
    assert np.isclose(s['ending_notes'].sum(),s['ending_asset'])
    assert np.isclose(s['ending_notes'].sum()+s['principal'].sum()+s['loss'].sum(),1000)
    assert np.isclose(s['principal'].sum(),s['scheduled']+s['prepaid']+s['recoveries'])
    assert np.all(s['ending_notes']>=0)

def test_sequential_principal_and_junior_first_losses():
    s=step(1000,[800,200],[.04,.08],60,0,.2)
    assert s['principal'][1]==0
    assert s['loss'][0]==0
    assert s['loss'][1]>0

def test_full_amortization_no_defaults():
    cf=project([800,200],[.04,.08],60,.08,0)
    assert np.isclose(cf.principal.sum(),1000)
    assert cf.loss.sum()==0

def test_interest_shortfall_is_visible():
    s=step(1000,[800,200],[.04,.08],60,0,0,asset_coupon=.001)
    assert s['interest'].sum()==0
    assert s['shortfall'].sum()>0

def test_single_payment_duration_analytical():
    cash=np.zeros(12);cash[-1]=100
    m=risk_measures(cash,cash,.05)
    assert np.isclose(m['pv'],100/1.05)
    assert np.isclose(m['duration'],1/1.05,rtol=1e-6)
    assert np.isclose(m['wal'],1)

def test_discounting_and_prepayment_direction():
    slow=project([800,200],[.04,.08],60,.02,0)
    fast=project([800,200],[.04,.08],60,.4,0)
    def wal(df):return risk_measures(df.interest+df.principal,df.principal,.05)['wal']
    assert wal(fast[fast.tranche=='A'])<wal(slow[slow.tranche=='A'])
    assert present_value([10,10],.1)<present_value([10,10],.01)

@pytest.mark.parametrize("annual",[-.1,1,2])
def test_invalid_probability(annual):
    with pytest.raises(ValueError):monthly_rate(annual)
