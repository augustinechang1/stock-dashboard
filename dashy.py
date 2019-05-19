import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import requests
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries
import plotly.graph_objs as go
from fbprophet import Prophet
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateFormatter, AutoDateLocator
import plotly.plotly as py
import plotly.tools as tls
import datetime
from dash.dependencies import Input, Output


r = requests.get('https://newsapi.org/v2/top-headlines?country=us&category=business&apiKey=c7ece947bed84fefa518b875c951322e')
json_data = r.json()["articles"]
news = pd.DataFrame(json_data)
news = pd.DataFrame(news[["title","url"]])

def generate_news_table(dataframe, max_rows=10):
    return html.Div(
        [
            html.Div(
                html.Table(
                    # Header
                    [html.Tr([html.Th()])]
                    +
                    # Body
                    [
                        html.Tr(
                            [
                                html.Td(
                                    html.A(
                                        dataframe.iloc[i]["title"],
                                        href=dataframe.iloc[i]["url"],
                                        target="_blank",
                                    )
                                )
                            ]
                        )
                        for i in range(min(len(dataframe), max_rows))
                    ]
                ),
                style={"height": "150px", "overflowY": "scroll"},
            ),
            html.P(
                "Last update : " + datetime.datetime.now().strftime("%H:%M:%S"),
                style={"fontSize": "11", "marginTop": "4", "color": "#45df7e"},
            ),
        ],
        style={"height": "100%"},
    )

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

ts = TimeSeries(key='X5AYBIDIH2EVGNW9', output_format='pandas')
df, meta_data = ts.get_daily(symbol='DJIA', outputsize='full')
df = df['4. close']
df = pd.DataFrame({'ds':df.index, 'y':df.values})
df['ds'] = pd.to_datetime(df['ds'])
df = df[(df['ds'] > '2014-05-10') & (df['ds'] < '2019-05-10')]

m = Prophet()
m.fit(df)
future = m.make_future_dataframe(periods=365)
forecast = m.predict(future)

def plot(
    m, fcst, ax=None, uncertainty=True, plot_cap=True, xlabel='ds', ylabel='y',
    figsize=(10, 6)
):
    """Plot the Prophet forecast.
    Parameters
    ----------
    m: Prophet model.
    fcst: pd.DataFrame output of m.predict.
    ax: Optional matplotlib axes on which to plot.
    uncertainty: Optional boolean to plot uncertainty intervals.
    plot_cap: Optional boolean indicating if the capacity should be shown
        in the figure, if available.
    xlabel: Optional label name on X-axis
    ylabel: Optional label name on Y-axis
    figsize: Optional tuple width, height in inches.
    Returns
    -------
    A matplotlib figure.
    """
    if ax is None:
        fig = plt.figure(facecolor='w', figsize=figsize)
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()
    fcst_t = fcst['ds'].dt.to_pydatetime()
    ax.plot(m.history['ds'].dt.to_pydatetime(), m.history['y'], 'k.')
    ax.plot(fcst_t, fcst['yhat'], ls='-', c='#0072B2')
    if 'cap' in fcst and plot_cap:
        ax.plot(fcst_t, fcst['cap'], ls='--', c='k')
    if m.logistic_floor and 'floor' in fcst and plot_cap:
        ax.plot(fcst_t, fcst['floor'], ls='--', c='k')
    if uncertainty:
        ax.fill_between(fcst_t, fcst['yhat_lower'], fcst['yhat_upper'],
                        color='#0072B2', alpha=0.2)
    # Specify formatting to workaround matplotlib issue #12925
    locator = AutoDateLocator(interval_multiples=False)
    formatter = AutoDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.grid(True, which='major', c='gray', ls='-', lw=1, alpha=0.2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    plotly_fig = tls.mpl_to_plotly(fig)
    return plotly_fig

a = plot(m, forecast)

app.layout = html.Div(children=[
    html.H1(children='Stock Dashboard'),

    html.Div(children='''
        News & Stock
    '''),


    dcc.Input(id='my-id', value='initial value', type='text'),
    html.Div(id='my-div'),

    dcc.Graph(
        id='example-graph',
        figure= go.Figure(
            data=a['data'],
            layout = go.Layout(
                autosize=False,
                width=500,
                height=500,
                margin=go.layout.Margin(
                    l=50,
                    r=50,
                    b=100,
                    t=100,
                    pad=4
                )
            )
            )
        ),
    generate_news_table(news)
])

@app.callback(
    Output('example-graph', 'figure'),
    [Input(component_id='my-id', component_property='value')]
)
def update_output_div(input_value):
    return 'You\'ve entered "{}"'.format(input_value)
def update_figure(input_value):
    df, meta_data = ts.get_daily(symbol=input_value, outputsize='full')
    df = df['4. close']
    df = pd.DataFrame({'ds':df.index, 'y':df.values})
    df['ds'] = pd.to_datetime(df['ds'])
    df = df[(df['ds'] > '2014-05-10') & (df['ds'] < '2019-05-10')]

    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=365)
    forecast = m.predict(future)
    a = plot(m, forecast)
    return {'data':a['data'],
        'layout' : go.Layout(
            autosize=False,
            width=500,
            height=500,
            margin=go.layout.Margin(
                l=50,
                r=50,
                b=100,
                t=100,
                pad=4))}


if __name__ == '__main__':
    app.run_server(debug=True)
