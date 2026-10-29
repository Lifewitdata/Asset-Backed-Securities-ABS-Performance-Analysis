"""Read-only Dash dashboard. Run the pipeline once before starting."""
from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash,Input,Output,dcc,html,dash_table
from .pipeline import ROOT


def create_app(root=ROOT):
    root=Path(root); out=root/"data/processed"
    required=["performance","securities","backtest","scenarios","model_metrics","manager_evaluation","holdings"]
    missing=[x for x in required if not (out/f"{x}.csv").exists()]
    if missing:
        raise FileNotFoundError("Run python -m abs_lab.pipeline first. Missing: "+", ".join(missing))
    frames={x:pd.read_csv(out/f"{x}.csv") for x in required}
    panel=frames["performance"].merge(frames["securities"],on="security_id")
    app=Dash(__name__,assets_folder=str(root/"assets"),title="ABS Research Lab")
    app.layout=html.Div([
        html.Div([html.Div("QUANTITATIVE RESEARCH / 01",className="eyebrow"),html.H1("ABS Research Lab"),
                  html.P("Cash flows, portfolio construction and credit risk in one research workspace.")],className="hero"),
        html.Div("SIMULATED DATA · Educational research · No live market feed",className="notice"),
        html.Div([
            html.Div([html.Label("Collateral sector"),dcc.Dropdown(["All"]+sorted(panel.sector.unique()),"All",id="sector",clearable=False)]),
            html.Div([html.Label("Note seniority"),dcc.Dropdown(["All","A","B"],"All",id="tranche",clearable=False)]),
            html.Div([html.Label("Stress scenario"),dcc.Dropdown(list(frames["scenarios"].scenario.unique()),"Credit stress",id="scenario",clearable=False)])
        ],className="controls"),
        html.Div(id="kpis",className="kpis"),
        html.Div([dcc.Graph(id="exposure"),dcc.Graph(id="stress")],className="grid"),
        html.H2("Portfolio and index research"),
        html.P("All-universe strategies, unaffected by the sector filters above. Monthly decisions use prior data; strategies include 10bp per unit of one-way turnover."),
        dcc.Graph(figure=px.line(frames["backtest"],x="date",y="wealth",color="portfolio",template="plotly_white",labels={"wealth":"Growth of 100"})),
        html.H2("Compare a portfolio"),
        dcc.Dropdown(sorted(frames["manager_evaluation"].portfolio),"Minimum variance",id="portfolio",clearable=False),
        html.Div(id="manager-stats"),dcc.Graph(id="weights"),
        html.H2("Time-series forecast evaluation"),
        html.P("One month ahead aggregate annual CDR. Errors shown in basis points; expanding-window evaluation against persistence."),
        dcc.Graph(figure=px.bar(frames["model_metrics"].assign(mae_bps=lambda d:d.mae*10000),x="model",y="mae_bps",template="plotly_white")),
        html.H2("Latest note-level data"),
        dash_table.DataTable(id="notes",page_size=12,sort_action="native",style_table={"overflowX":"auto"},
                             style_cell={"fontFamily":"Arial","fontSize":13,"padding":"10px","textAlign":"left"}),
        html.Footer("Model limits: straight-line collateral amortization, instant recoveries and fixed future CPR/CDR. Duration holds projected cash flows fixed. Read docs/methodology.md before interpreting results.")
    ],className="shell")

    @app.callback(Output("kpis","children"),Output("exposure","figure"),Output("stress","figure"),
                  Output("notes","data"),Output("notes","columns"),
                  Input("sector","value"),Input("tranche","value"),Input("scenario","value"))
    def update(sector,tranche,scenario):
        latest=panel[panel.date==panel.date.max()].copy()
        if sector!="All":latest=latest[latest.sector==sector]
        if tranche!="All":latest=latest[latest.tranche==tranche]
        total=latest.market_value.sum()
        duration=(latest.duration*latest.market_value).sum()/total if total else 0.
        yield_=(latest["yield"]*latest.market_value).sum()/total if total else 0.
        stress=frames["scenarios"]
        stress=stress[(stress.scenario==scenario)&stress.security_id.isin(latest.security_id)]
        cards=[("Market value",f"${total/1e6:,.1f}m"),("Weighted duration",f"{duration:.2f} years"),
               ("Discount yield",f"{yield_:.2%}"),("Scenario P&L",f"${stress.pnl.sum()/1e6:,.2f}m")]
        kpis=[html.Div([html.Span(label),html.Strong(value)],className="card") for label,value in cards]
        exposure=px.bar(latest.groupby(["sector","tranche"],as_index=False).market_value.sum(),x="sector",y="market_value",color="tranche",template="plotly_white",title="Market value by collateral")
        stressfig=px.bar(stress,x="security_id",y="pnl",color="tranche",template="plotly_white",title=scenario+" — full repricing")
        cols=["security_id","sector","tranche","rating","balance","market_value","yield","duration","wal"]
        table=latest[cols].round(4)
        return kpis,exposure,stressfig,table.to_dict("records"),[{"name":c.replace("_"," ").title(),"id":c} for c in cols]

    @app.callback(Output("manager-stats","children"),Output("weights","figure"),Input("portfolio","value"))
    def manager(name):
        row=frames["manager_evaluation"].set_index("portfolio").loc[name]
        h=frames["holdings"];h=h[(h.portfolio==name)&(h.date==h.date.max())]
        text=f"CAGR {row.cagr:.2%} · Annual volatility {row.annual_volatility:.2%} · Maximum drawdown {row.max_drawdown:.2%} · Tracking error {row.tracking_error:.2%}"
        return html.P(text),px.bar(h,x="security_id",y="weight",template="plotly_white",title="Latest rebalance weights (prior month information)")
    # Pure callback handles exposed for direct numerical smoke tests, no web side effects.
    app.abs_update=update;app.abs_manager=manager
    return app

if __name__=="__main__":
    create_app().run(host="127.0.0.1",port=8050,debug=False)
