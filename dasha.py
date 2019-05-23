import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import requests
import plotly.graph_objs as go
from fbprophet import Prophet
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateFormatter, AutoDateLocator
import plotly.plotly as py
import plotly.tools as tls
import datetime
from dash.dependencies import Input, Output, State
from iexfinance.stocks import get_historical_data
from iexfinance import Stock
import dash_table_experiments as dt
import dash_table

b = Stock('goog')
d = b.get_news()
df = pd.DataFrame(d)
df = df[['headline', 'url']]
e = pd.DataFrame([b.get_key_stats()])
e = e[['EBITDA', 'beta', 'latestEPS', 'marketcap']]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div([

    html.Div(children='''
        Enter stock symbol
    '''),

    dcc.Input(id='input-1-state', value='', type='text'),

    html.Button(id='submit', n_clicks=0, children='Submit'),

    html.H1(id='name', children='Stock Dashboard'),

    dcc.Checklist(
        id='checkbox',
        options=[
            {'label': 'Forecast', 'value': 'ts'}
    ], values=[]),


    html.Div([
        html.Div([
            html.Div([
                html.P('About',style={"fontSize":"13","color":"#45df7e"}),
                html.Div(id='description', children='company description'),

                html.Div(
                    dash_table.DataTable(
                    id='metadata',
                    style_cell_conditional=[
                        {'if': {'column_id': 'EBITDA'},
                         'width': '110px'},
                        {'if': {'column_id': 'beta'},
                         'width': '110px'},
                        {'if': {'column_id': 'latestEPS'},
                        'width': '110px'},
                        {'if': {'column_id': 'marketcap'},
                        'width': '110px'},
                    ],
                    columns=[{"name": i, "id": i} for i in e.columns],
                    data=e.to_dict('records'),
                    style_header={'backgroundColor': '#18252E'},
        style_cell={
            'backgroundColor': '#18252E',
            'color': 'white'}))]
            , style={'width': '49%', 'height': '500px', 'display': 'inline-block', 'float': 'left', "height":"33%",
            "backgroundColor": "#18252E",
            "color": "white",
            "fontSize": "13",
            "padding":"10px 10px 10px 10px",
            "marginTop":"5",
            "marginBottom":"0"})
                ,    dcc.Graph(
                        id='graph',
                        figure={'data':[],
                             'layout': {
                                    'plot_bgcolor': "#18252E",
                                    'paper_bgcolor': "#18252E",
                                    'font': {
                                        'color': 'white'
                                    }}},
                        style={'width': '49%', 'display': 'inline-block', 'float': 'right', "backgroundColor": "#18252E", "color": "white",}),
        html.Div([

                html.P('Headlines',style={"fontSize":"13","color":"#45df7e"}),
                html.Div([
                    html.Table(
                        [
                            html.Tr(
                                [
                                    html.Td(
                                        html.A(
                                            df.iloc[i]["headline"],
                                            href=df.iloc[i]["url"],
                                            target="_blank",
                                        )
                                    )
                                ]
                            )
                            for i in range(min(len(df), 10))
                        ], id='table',
                        ),
                        ], style={"height": "250px", "overflowY": "scroll"})], style={'width': '49%', 'display': 'inline-block', 'float': 'left', "height":"33%",
                        "backgroundColor": "#18252E",
                        "color": "white",
                        "fontSize": "13",
                        "padding":"10px 10px 0px 10px",
                        "marginTop":"5",
                        "marginBottom":"0"})])



], style={'width': '100%', 'display': 'inline-block'}),
    ],
    style={"padding": "0", "height": "100vh", "backgroundColor": "#1a2d46", 'color': 'white'},)

#Company Name
@app.callback(
    Output('name', 'children'),
    [Input('submit', 'n_clicks')],
    [State('input-1-state', 'value')]
)

def update_header(submit, input_value):

    b = Stock(input_value)
    name = pd.DataFrame([b.get_company()])
    name = name['companyName'].values[0]
    f = str(b.get_price())
    title = name + ' $'+ f
    return title

#Company Description
@app.callback(
    Output('description', 'children'),
    [Input('submit', 'n_clicks')],
    [State('input-1-state', 'value')]
)

def update_header(submit, input_value):

    b = Stock(input_value)
    name = pd.DataFrame([b.get_company()])
    description = name['description']

    return description

#Update news
@app.callback(
    Output('table', 'children'),
    [Input('submit', 'n_clicks')],
    [State('input-1-state', 'value')]
)

def update_table(submit, input_value):

    b = Stock(input_value)
    d = b.get_news()
    df = pd.DataFrame(d)
    df = df[['headline', 'url']]

    name = pd.DataFrame([b.get_company()])
    name = name['companyName']

    return [
            html.Tr(
                [
                    html.Td(
                        html.A(
                            df.iloc[i]["headline"],
                            href=df.iloc[i]["url"],
                            target="_blank",
                        )
                    )
                ]
            )
            for i in range(min(len(df), 10))
        ]

#Update graph
@app.callback(
    Output('graph', 'figure'),
    [Input('submit', 'n_clicks'),
     Input('checkbox', 'values')],
    [State('input-1-state', 'value')]
)

def update_figure(submit, checkbox, input_value):

    traces = []
    start = datetime.datetime(2016, 1, 1)
    end =  datetime.datetime.now()
    f = get_historical_data(input_value, start, end, output_format='pandas')
    f = f['close']
    df = pd.DataFrame({'ds':f.index, 'y':f.values})
    actual = go.Scatter(
                    x=df['ds'],
                    y=df['y'],
                    name = 'closing'
    )

    traces.append(actual)
    m = Prophet()

    if checkbox:

        m.fit(df)
        future = m.make_future_dataframe(periods=120)
        forecast = m.predict(future)
        forecast = forecast.set_index('ds')
        forecast_valid = forecast['yhat']
        forecast_valid = pd.DataFrame(forecast_valid)

        forecast = go.Scatter(
                        x=forecast_valid.index,
                        y=forecast_valid['yhat'],
                        name ='forecast'
        )
        traces.append(forecast)

    a = {
        'data': traces,
        'layout': go.Layout(
            {
                   'plot_bgcolor': "#18252E",
                   'paper_bgcolor': "#18252E",
                   'font': {
                       'color': 'white'}}
        )
    }

    return a



if __name__ == '__main__':
    app.run_server(debug=True)
