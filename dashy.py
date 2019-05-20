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
from dash.dependencies import Input, Output
from iexfinance.stocks import get_historical_data

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
                style={"height": "550px", "width": "500px", "overflowY": "scroll"},
            ),
            html.P(
                "Last update : " + datetime.datetime.now().strftime("%H:%M:%S"),
                style={"fontSize": "11", "marginTop": "4", "color": "#45df7e"},
            ),
        ],
        style={"height": "100%", 'display': 'inline-block'},
    )

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

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

app.layout = html.Div([
    html.H1(children='Stock Dashboard'),

    html.Div(children='''
        Enter stock symbol for 1 year forecast
    '''),

    dcc.Input(id='my-id', value='spy', type='text'),
    html.Div([
        generate_news_table(news),
        dcc.Graph(
            id='example-graph',
                figure={'layout': {'height': 600, 'width': 600}}, style={'display': 'inline-block'}
                    )], style={'width': '100%', 'display': 'inline-block'})
    ])

@app.callback(
    Output('example-graph', 'figure'),
    [Input('my-id', 'value')]
)

def update_figure(input_value):

    start = datetime.datetime(2016, 5, 20)
    end = datetime.datetime(2019, 5, 20)
    f = get_historical_data(input_value, start, end, output_format='pandas')
    f = f['close']
    df = pd.DataFrame({'ds':f.index, 'y':f.values})

    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=365)
    forecast = m.predict(future)
    a = plot(m, forecast)
    return {'data':go.Figure(a['data'])}


if __name__ == '__main__':
    app.run_server(debug=True)
