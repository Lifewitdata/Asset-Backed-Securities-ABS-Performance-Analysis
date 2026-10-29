"""Expanding-window, one-month-ahead aggregate CDR forecasts; no random time split."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


def feature_table(pool,macro):
    # Simple equal-deal aggregate, explicitly distinct from balance-weighted CDR.
    ts=pool.groupby("date").cdr.mean().to_frame().join(macro.set_index("date")[["unemployment","base_rate"]])
    ts["cdr_lag1"]=ts.cdr.shift(1)
    ts["cdr_mean3"]=ts.cdr.rolling(3).mean()
    ts["target"]=ts.cdr.shift(-1)
    ts["target_date"]=pd.Series(ts.index,index=ts.index).shift(-1)
    return ts.dropna()


def forecast(pool,macro):
    table=feature_table(pool,macro)
    columns=["cdr","cdr_lag1","cdr_mean3","unemployment","base_rate"]
    rows=[]
    # Fixed hyperparameters, 36-month initial training period. Retrain each month.
    for i in range(36,len(table)):
        train=table.iloc[:i]; test=table.iloc[[i]]
        # Prior month's target is known at this month's decision date.
        if train.target_date.max()>test.index[0]:
            raise ValueError("Future target leakage")
        ols=sm.OLS(train.target,sm.add_constant(train[columns],has_constant="add")).fit()
        forest=RandomForestRegressor(n_estimators=80,max_depth=3,min_samples_leaf=5,random_state=42,n_jobs=1)
        forest.fit(train[columns],train.target)
        predictions={"Persistence":float(test.cdr.iloc[0]),
                     "OLS":float(ols.predict(sm.add_constant(test[columns],has_constant="add")).iloc[0]),
                     "Random forest":float(forest.predict(test[columns])[0])}
        for model,value in predictions.items():
            rows.append({"decision_date":test.index[0],"target_date":test.target_date.iloc[0],
                         "last_training_target_date":train.target_date.max(),"model":model,
                         "actual":test.target.iloc[0],"predicted":np.clip(value,0,.999)})
    predictions=pd.DataFrame(rows)
    metrics=[]
    for model,g in predictions.groupby("model"):
        metrics.append({"model":model,"mae":mean_absolute_error(g.actual,g.predicted),
                        "rmse":np.sqrt(mean_squared_error(g.actual,g.predicted)),"observations":len(g)})
    return predictions,pd.DataFrame(metrics)
