"""One command creates data, validates, analyses, backtests and writes reports."""
import argparse
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
from .data import generate,clean
from .portfolio import backtest,evaluate,stress
from .models import forecast

ROOT=Path(__file__).resolve().parents[2]


def run(root=ROOT,regenerate=False):
    root=Path(root); out=root/"data/processed"; report=root/"reports"
    out.mkdir(parents=True,exist_ok=True); report.mkdir(parents=True,exist_ok=True)
    if regenerate or not (root/"data/raw/monthly_performance.csv").exists():
        generate(root)
    sec,panel,pool,macro,quality=clean(root)
    bt,holdings=backtest(sec,panel)
    performance=evaluate(bt)
    scenarios=stress(sec,panel,pool)
    predictions,metrics=forecast(pool,macro)
    for name,frame in {"securities":sec,"performance":panel,"pool_performance":pool,"macro":macro,
                       "backtest":bt,"holdings":holdings,"manager_evaluation":performance,
                       "scenarios":scenarios,"predictions":predictions,"model_metrics":metrics}.items():
        frame.to_csv(out/f"{name}.csv",index=False,float_format="%.10f")
    (report/"data_quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    px.line(bt,x="date",y="wealth",color="portfolio",title="Simulated portfolios — growth of 100").write_html(report/"portfolio_performance.html",include_plotlyjs="cdn")
    px.bar(scenarios.groupby("scenario",as_index=False).pnl.sum(),x="scenario",y="pnl",title="Simulated universe — scenario P&L ($)").write_html(report/"stress_scenarios.html",include_plotlyjs="cdn")
    summary={"data_type":"synthetic", "securities":quality["securities"],"clean_rows":quality["clean_rows"],
             "backtest_months":bt.date.nunique(),"best_forecast_by_mae":metrics.sort_values("mae").iloc[0].model}
    (report/"research_facts.json").write_text(json.dumps(summary,indent=2)+"\n")
    index=performance.set_index("portfolio").loc["ABS Index"]
    mv=performance.set_index("portfolio").loc["Minimum variance"]
    worst=scenarios.groupby("scenario").pnl.sum().sort_values().iloc[0]
    best=metrics.sort_values("mae").iloc[0]
    text=f"""# ABS research brief

**Demonstration only: all securities, prices, macro data and results are simulated.**

## Question
How do credit losses, prepayments and interest rates affect a securitized-credit portfolio, and can allocation constraints reduce measured risk?

## Findings from this run
- The dataset contains {quality['securities']} notes across 12 pools and {quality['months']} month-end snapshots. Validation removed {quality['exact_duplicates_removed']} exact duplicate; balances reconcile after principal payments and write-downs.
- Over {bt.date.nunique()} out-of-sample monthly observations, the illustrative ABS index returned {index.cagr:.2%} annualised with {index.annual_volatility:.2%} volatility. The constrained minimum-variance strategy returned {mv.cagr:.2%}, with {mv.annual_volatility:.2%} volatility after modelled trading costs.
- The most adverse defined scenario changes the full remaining universe's value by ${worst:,.0f}. This is a repricing scenario, not a probability-weighted loss forecast.
- The lowest forecast MAE belongs to **{best.model}** at {best.mae*10000:.2f} basis points of annual CDR. Compare all models against persistence; complexity alone is not evidence of value.

## Practical interpretation
Inspect junior-note losses and extension sensitivity before choosing an allocation. Use issuer/deal diversification and client constraints in addition to historical volatility. Do not infer manager skill from the three rule-based demonstration portfolios.

## Limits
Fixed cohort, simplified two-note waterfall, instant recoveries, constant forward prepayment/default assumptions, no taxes or liquidity model. Simulated relationships make both backtests and ML results unsuitable as estimates of real-market performance. SQL Server integration requires a separate configured server. See docs/methodology.md.

## Supporting outputs
- [Portfolio chart](portfolio_performance.html)
- [Scenario chart](stress_scenarios.html)
- Numeric results: data/processed/manager_evaluation.csv and model_metrics.csv.
"""
    (report/"executive_summary.md").write_text(text)
    print(json.dumps(summary,indent=2))
    return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--regenerate",action="store_true",help="Overwrite simulated raw inputs with seeded demo data")
    args=parser.parse_args();run(regenerate=args.regenerate)
