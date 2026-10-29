import pytest
from abs_lab.dashboard import create_app

@pytest.fixture(scope='module')
def app():return create_app()

@pytest.mark.parametrize('route',['/','/_dash-layout','/_dash-dependencies','/assets/style.css'])
def test_http_routes(app,route):
    response=app.server.test_client().get(route)
    assert response.status_code==200

@pytest.mark.parametrize('sector',['All','Auto','Equipment','Consumer'])
@pytest.mark.parametrize('tranche',['All','A','B'])
def test_filters_return_real_rows(app,sector,tranche):
    cards,exposure,stress,data,columns=app.abs_update(sector,tranche,'Credit stress')
    assert len(cards)==4 and data and columns
    if sector!='All':assert all(x['sector']==sector for x in data)
    if tranche!='All':assert all(x['tranche']==tranche for x in data)
    assert len(stress.data)>0 and len(exposure.data)>0

@pytest.mark.parametrize('portfolio',['ABS Index','Defensive','Income','Minimum variance'])
def test_portfolio_callback(app,portfolio):
    text,fig=app.abs_manager(portfolio)
    assert 'CAGR' in text.children and len(fig.data)>0

def test_dash_callback_transport(app):
    key=next(k for k in app.callback_map if 'kpis' in k)
    outputs=[{'id':i,'property':p} for i,p in [('kpis','children'),('exposure','figure'),('stress','figure'),('notes','data'),('notes','columns')]]
    response=app.server.test_client().post('/_dash-update-component',json={
        'output':key,'outputs':outputs,'inputs':[{'id':i,'property':'value','value':v} for i,v in [('sector','Auto'),('tranche','A'),('scenario','Rates +100bp')]],'state':[],'changedPropIds':['sector.value']})
    assert response.status_code==200
    assert len(response.get_json()['response']['notes']['data'])==4
