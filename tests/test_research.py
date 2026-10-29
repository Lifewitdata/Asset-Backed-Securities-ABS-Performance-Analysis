import json
import numpy as np
import pandas as pd
import pytest
from abs_lab.pipeline import ROOT
from abs_lab.data import clean,validate
from abs_lab.portfolio import backtest,optimise
from abs_lab.models import feature_table
from abs_lab.database import merge_sql
from abs_lab.ai_brief import validate_response

@pytest.fixture(scope='module')
def data():return clean(ROOT)

def test_duplicate_cleaning_and_returns(data):
    sec,panel,pool,macro,quality=data
    assert quality['exact_duplicates_removed']==1
    assert len(panel)==24*73
    assert panel.total_return.isna().sum()==24
    g=panel[panel.security_id=='DEAL01-A']
    expected=(g.market_value.iloc[1]+g.interest.iloc[1]+g.principal.iloc[1])/g.market_value.iloc[0]-1
    assert np.isclose(g.total_return.iloc[1],expected)

@pytest.mark.parametrize('failure',['unknown','duplicate','negative','reconciliation','missing_month','nonfinite'])
def test_corrupt_input_rejected(data,failure):
    sec,panel,pool,macro,_=data
    panel=panel.drop(columns='total_return').copy()
    if failure=='unknown':panel.loc[panel.index[0],'security_id']='UNKNOWN'
    if failure=='duplicate':panel=pd.concat([panel,panel.iloc[[0]]])
    if failure=='negative':panel.loc[panel.index[0],'interest']=-1
    if failure=='reconciliation':panel.loc[panel.index[0],'balance']+=100
    if failure=='missing_month':panel=panel.iloc[1:]
    if failure=='nonfinite':panel.loc[panel.index[0],'yield']=np.inf
    with pytest.raises(ValueError):validate(sec,panel,pool,macro)

def test_index_weights_costs_and_lag():
    path=ROOT/'data/processed'
    bt=pd.read_csv(path/'backtest.csv',parse_dates=['date','decision_date'])
    h=pd.read_csv(path/'holdings.csv',parse_dates=['date','decision_date'])
    assert (bt.decision_date<bt.date).all()
    assert np.allclose(h.groupby(['date','portfolio']).weight.sum(),1)
    assert h.weight.min()>=0
    assert h[h.portfolio=='Minimum variance'].weight.max()<=.15001
    assert (bt[bt.portfolio=='ABS Index'].cost==0).all()
    assert np.allclose(bt.gross_return-bt.net_return,bt.cost)
    assert (bt.turnover.between(0,1+1e-8)).all()

def test_backtest_is_invariant_to_future_data(data):
    sec,panel,*_=data
    cutoff=pd.Timestamp('2022-06-30')
    short,_=backtest(sec,panel[panel.date<=cutoff])
    full=pd.read_csv(ROOT/'data/processed/backtest.csv',parse_dates=['date','decision_date'])
    expected=full[full.date<=cutoff].reset_index(drop=True)
    pd.testing.assert_frame_equal(short.reset_index(drop=True),expected,check_dtype=False,atol=1e-8,rtol=1e-6)

def test_forecast_features_are_past_only(data):
    _,_,pool,macro,_=data
    cutoff=pd.Timestamp('2023-01-31')
    before=feature_table(pool,macro)
    changed=pool.copy();changed.loc[changed.date>cutoff,'cdr']=.9
    after=feature_table(changed,macro)
    cols=['cdr','cdr_lag1','cdr_mean3','unemployment','base_rate']
    pd.testing.assert_frame_equal(before.loc[:cutoff,cols],after.loc[:cutoff,cols])
    predictions=pd.read_csv(ROOT/'data/processed/predictions.csv',parse_dates=['decision_date','target_date','last_training_target_date'])
    assert (predictions.last_training_target_date<=predictions.decision_date).all()
    assert (predictions.target_date>predictions.decision_date).all()

def test_stress_base_reconciles():
    s=pd.read_csv(ROOT/'data/processed/scenarios.csv')
    assert np.allclose(s[s.scenario=='Base'].pnl,0,atol=.2)
    assert s[s.scenario=='Rates +100bp'].pnl.sum()<0

def test_infeasible_allocation_is_not_silently_replaced(data):
    sec,panel,*_=data
    r=panel.pivot(index='date',columns='security_id',values='total_return').iloc[1:25]
    s=panel[panel.date==panel.date.min()].merge(sec,on='security_id').set_index('security_id').reindex(r.columns)
    with pytest.raises(ValueError):optimise(r,s,max_weight=.01)

def test_sql_merge_is_keyed_and_identifier_safe():
    query=merge_sql('Security','stage_abs_x',['security_id','coupon'],['security_id'])
    assert 'HOLDLOCK' in query and 'WHEN MATCHED' in query and 't.[security_id]=s.[security_id]' in query
    with pytest.raises(ValueError):merge_sql('Security;DROP TABLE x','s',['x'],['x'])

def test_ai_grounding_rejects_invented_metrics():
    facts={'securities':24}
    good={'claims':[{'metric_key':'securities','value':24,'explanation':'Simulated notes'}]}
    assert validate_response(good,facts)==good
    good['claims'][0]['value']=99
    with pytest.raises(ValueError):validate_response(good,facts)
