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

b = Stock('spy')
d = b.get_news()
df = pd.DataFrame(d)
df = df[['headline', 'url']]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1(children='Stock Dashboard'),

    html.Div(children='''
        Enter stock symbol
    '''),

    dcc.Input(id='input-1-state', value='initial value', type='text'),

    html.Button(id='submit-button', n_clicks=0, children='Submit'),

    dcc.Dropdown(
        id='my-dropdown',
        options=[]),

    html.Div([
        # html.Div(id="table"),
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
            ], id='table', style={'display': 'inline-block'}
            ),
        dcc.Graph(
            id='graph', style={'display': 'inline-block'})], style={'width': '100%', 'display': 'inline-block'})
    ])


@app.callback(
    Output('my-dropdown', 'options'),
    [Input('submit-button', 'n_clicks')],
    [State('input-1-state', 'value')]
)
def update_dropdown(n_clicks, input_value):
    return [{'label': str(input_value), 'value': str(input_value)}]

@app.callback(
    Output('table', 'children'),
    [Input('my-dropdown', 'value')])

def update_table(input_value):

    b = Stock(input_value)
    d = b.get_news()
    df = pd.DataFrame(d)
    df = df[['headline', 'url']]

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

@app.callback(
    Output('graph', 'figure'),
    [Input('my-dropdown', 'value')]
)

def update_figure(input_value):

    start = datetime.datetime(2016, 5, 20)
    end = datetime.datetime(2019, 5, 20)
    f = get_historical_data(input_value, start, end, output_format='pandas')

    a = {'data':go.Figure(
                data=[
                    go.Candlestick(
                        x=f.index,
                        open=f['open'],
                        high=f['high'],
                        low=f['low'],
                        close=f['close']
                )
                ]
            )}

    return a


if __name__ == '__main__':
    app.run_server(debug=True)
