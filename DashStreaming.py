import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dte
import pandas as pd
import plotly
import plotly.graph_objs as go
from dash.dependencies import Output, Input

import refinitiv.dataplatform as rdp
import configparser as cp

global esg_df, tick_list, streaming_price, streaming_news, news_history
# Streaming related
ric_list = ['EUR=', 'AUD=','JPY=', 'BP.L', 'BT.L']
stream_fields = ['DSPLY_NAME','OPEN_PRC', 'HST_CLOSE', 'BID', 'BIDSIZE' ,'ASK', 'ASKSIZE', 'ACVOL_1', 'TRDPRC_1', 'TRDTIM_1', 'MID_PRICE']
tick_field = 'MID_PRICE'
prev_ric = ric_list[0]

# News related
news_ric = 'NFCP_UBMS'
news_fields = ['PNAC', 'HEADLINE1', 'NEWSCODE01']

# Called first time the app is run and also when the dropdown list is changed
def get_data(ric, initial_run=False):
    global esg_df, tick_list, streaming_price, streaming_news, news_history
        
    if initial_run:
        # ESG DATA
        esg_df = rdp.get_esg_standard_scores(universe='VOD.L')
        # Streaming News
        streaming_news = rdp.StreamingPrices(universe=[news_ric], fields=news_fields)
        streaming_news.open()
        news_history = streaming_news.get_snapshot()
        
    # Price History
    tick_hist_df = rdp.get_historical_price_events(ric, fields=[tick_field], count=200)
    tick_list = pd.to_numeric(tick_hist_df[tick_field]).to_list()
    tick_list.reverse()
    # Streaming Price
    streaming_price = rdp.StreamingPrices(universe=[ric], fields=stream_fields)
    streaming_price.open()

# Open session to Refinitiv Data Platform (Cloud) Server
config = cp.ConfigParser()
config.read("config.cfg")
rdp.open_platform_session(
    config['session']['app_key'],
    rdp.GrantPassword(
        username=config['session']['user'],
        password=config['session']['password']
    )
)
get_data(ric_list[0], True)

# DASH FRAMEWORK CODE
app = dash.Dash("RDP Dashboard")
app.layout = html.Div([

    html.H2('Streaming Dashboard Example', style={'color': 'blue'}),
    html.Div(id='nop1'),
    dcc.Dropdown(id='ric-dropdown',
                 options=[{'label': i, 'value': i} for i in ric_list],
                 value=ric_list[0]),
    html.Div(id='nop2'),
    html.H4('Streaming Graph'),
    dcc.Graph(id='live-graph', animate=True),
    dcc.Interval(id='stream-update', interval=1 * 1000),

    html.H4('Streaming Fields'),
    dte.DataTable(id='tickData',
                  columns=[{'name': i, 'id': i} for i in stream_fields]),

    html.H4('Streaming News'),
    dte.DataTable(id='newsData',
                  columns=[{'name': i, 'id': i} for i in news_fields],
                  style_cell={'textAlign': 'left'},
                  page_size=5),
    
    html.H4('Non-Streaming data e.g. ESG Standard Scores for Vodafone'),
    dte.DataTable(id='esgData',
                   columns=[{"name": a, "id": a} for a in esg_df],
                   data=esg_df.to_dict('records'),
                   style_table={'overflowX': 'auto'}
                   ),

])

@app.callback([Output('live-graph', 'figure'),
               Output('tickData', 'data'),
               Output('newsData', 'data') ],
              [Input('ric-dropdown', 'value'),
               Input('stream-update', 'n_intervals')])
def update_ric(selected_ric, input_data):
    global prev_ric, news_history, tick_list
    # could have used callback-context?
    if selected_ric == prev_ric: 
        tick_list.pop(0)
        tick_list.append(streaming_price.get_snapshot()[tick_field].iloc[0])
    else:
        print("RIC change from {} to {}".format(prev_ric, selected_ric))
        prev_ric = selected_ric
        get_data(selected_ric)
        
    streaming_fields = streaming_price.get_snapshot()

    latest_news = streaming_news.get_snapshot()
    if not latest_news['PNAC'].iloc[0] == news_history['PNAC'].iloc[0]:
        news_history = latest_news.append(news_history)

    data = plotly.graph_objs.Scatter(
        y=tick_list,
        name='Scatter',
        mode='lines+markers'
    )
    return {'data': [data], 'layout': go.Layout(yaxis={'title': 'MID',
                                                       'range': [min(tick_list) * 0.9994, max(tick_list) * 1.0006]})}, \
           streaming_fields.to_dict('records'), news_history.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)
