import datetime as dt
from dateutil import parser

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Input, Output, State

from api import get_assets, get_fear_greed_data, get_rsi_data
from constants import CURRENCY_SYMBOLS, COLORS
from layout.main_layout import render_layout
from utils import clean_price_data, clean_ma_data, clean_exchange_rates


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True


DF_CRYPTO_ASSETS = get_assets()
CRYPTO_ASSET_NAMES = DF_CRYPTO_ASSETS.loc[:, 'id'].to_list()
FIAT_CURRENCY_RATES = clean_exchange_rates(
    date=dt.date.today(), 
    currency_names=['USD', 'EUR', 'GBP', 'PLN', 'CHF']
)

##### Main crypto graph section #####
DF_MAIN_GRAPH = clean_price_data(
    start=dt.datetime(2015, 1, 1),
    end=dt.datetime.now(),
    currencies=CRYPTO_ASSET_NAMES
)


@app.callback(
    Output("crypto-graph", "figure"),
    [
        Input("crypto-dropdown", "value"),
        Input('base-currency', 'value'),
        Input('start-date-picker', 'date'),
        Input('end-date-picker', 'date')
    ]
)
def display_main_crypto_series(crypto_dropdown, base_currency, start_date, end_date):
    start_time = parser.isoparse(start_date)
    end_time = parser.isoparse(end_date)
    fiat_curr_rate = FIAT_CURRENCY_RATES[base_currency]
    df = (
        DF_MAIN_GRAPH
        .loc[lambda x: x['timestamp'].between(start_time, end_time)]
        .set_index('timestamp')
        .multiply(fiat_curr_rate)
        .reset_index()
        .rename(columns={'timestamp': 'date'})
    )
    fig = px.line(
        df,
        x='date',
        y=crypto_dropdown,
        labels={
            "bitcoin": "Price",
            "value": "Price",
            "date": "Date"
        }
    )
    fig.layout.plot_bgcolor = COLORS['background']
    fig.layout.paper_bgcolor = COLORS['background']
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


@app.callback(
    [
        Output('LED-display-usd', 'value'),
        Output('LED-display-pln', 'value'),
        Output('LED-display-eur', 'value'),
        Output('LED-display-gpb', 'value'),
        Output('LED-display-chf', 'value'),
        Output('alert', 'children'),
        Output('alert', 'color'),
        Output('alert', 'is_open')
    ],
    [Input('base-currency', 'value')]
)
def display_exchange_rates(base_currency):
    fiat_curr_rate = FIAT_CURRENCY_RATES[base_currency]
    updated_rates = {
        label: round((value / fiat_curr_rate), 2) 
        for label, value in FIAT_CURRENCY_RATES.items()
    }
    usd_rate = updated_rates['USD']
    pln_rate = updated_rates['PLN']
    eur_rate = updated_rates['EUR']
    gbp_rate = updated_rates['GBP']
    chf_rate = updated_rates['CHF']
    alert_message = "Everything ok"
    color = "info"
    is_open = False
    return usd_rate, pln_rate, eur_rate, gbp_rate, chf_rate, alert_message, color, is_open


@app.callback(
    Output('table-header', 'children'),
    [Input('base-currency', 'value')]
)
def display_ranking_table_header(base_currency):
    return f'Ranking of 10 ten most popular cryptocurrencies in {base_currency}:'


@app.callback(
    [
        Output('crypto-table', 'columns'),
        Output('crypto-table', 'data')
    ],
    [Input('base-currency', 'value')]
)
def display_ranking_table_body(base_currency):
    curr_symbol = CURRENCY_SYMBOLS[base_currency]
    fiat_curr_rate = FIAT_CURRENCY_RATES[base_currency]
    df_cleaned = (
        DF_CRYPTO_ASSETS
        .assign(
            priceUsd=lambda x: x['priceUsd'] * fiat_curr_rate,
            marketCapUsd=lambda x: x['marketCapUsd'] * fiat_curr_rate,
            Logo=lambda x: (
                '[![Coin](https://cryptologos.cc/logos/' +
                x["id"] + "-" + x["symbol"].str.lower() +
                '-logo.svg?v=023#thumbnail)](https://cryptologos.cc/)'
            ),
        )
        .round({
            'priceUsd': 4,
            'supply': 2,
            'marketCapUsd': 2,
            'changePercent24Hr': 2,
        })
        .rename(columns={
            'rank': 'Pos',
            'name': 'Crypto Name',
            'symbol': 'Symbol',
            'priceUsd': f'Price[{curr_symbol}]',
            'marketCapUsd': f'MarketCap[{curr_symbol}]',
            'supply': 'Supply',
            'changePercent24Hr': "Change24h[%]",
        })
        .reindex(columns=[
            'Pos', 'Logo', 'Crypto Name', 'Symbol',
            f'Price[{curr_symbol}]', 'Supply',
            f'MarketCap[{curr_symbol}]', 'Change24h[%]'
        ])
    )
    data = df_cleaned.to_dict('records')
    columns = []
    for col_name in df_cleaned.columns.to_list():
        if col_name == 'Logo':
            columns.append({
                'id': col_name, 
                'name': col_name,
                'presentation': 'markdown',
            })
        else:
            columns.append({
                'id': col_name, 
                'name': col_name,
            })
    return (columns, data)


##### Fear and greed index section #####
df_fng = get_fear_greed_data()

@app.callback(
    Output("fng-collapse", "is_open"),
    [Input("fng-collapse-button", "n_clicks")],
    [State("fng-collapse", "is_open")],
)
def fng_toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("fng-line-graph", "figure"),
    Input("fng-checklist", "value")
)
def display_fng_series(time_range):
    if time_range == "Last Week":
        df_cut = df_fng[:6]
    elif time_range == "Last Month":
        df_cut = df_fng[:29]
    elif time_range == "Last Six Month":
        df_cut = df_fng[:179]
    else:
        df_cut = df_fng
    fig = px.line(
        df_cut,
        x='timestamp',
        y='value',
        labels={
            "value": "FNG value",
            "timestamp": "Date"
        }
    )
    fig.layout.plot_bgcolor = COLORS['background']
    fig.layout.paper_bgcolor = COLORS['background']
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


###### RSI indicator section #######
df_rsi = get_rsi_data()


@app.callback(
    Output("rsi-line-graph", "figure"),
    Input("rsi-checklist", "value")
)
def display_rsi_series(time_range):
    if time_range == "Last Day":
        df_cut = df_rsi[:25]
    elif time_range == "Last Week":
        df_cut = df_rsi[:169]
    elif time_range == "Last Two Weeks":
        df_cut = df_rsi[:337]
    else:
        df_cut = df_rsi
    fig = px.scatter(
        df_cut,
        x="timestamp",
        y="value",
        color="value",
        color_continuous_scale=["red", "yellow", "green"],
        title="RSI Index for X:BTC-USD indicator",
        labels={
            "value": "RSI value",
            "timestamp": "Date"
        }
    )
    fig.layout.plot_bgcolor = COLORS['background']
    fig.layout.paper_bgcolor = COLORS['background']
    fig.update_traces(mode='markers+lines')
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


@app.callback(
    Output("rsi-collapse", "is_open"),
    [Input("rsi-collapse-button", "n_clicks")],
    [State("rsi-collapse", "is_open")],
)
def rsi_toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


###### MA-50 and Ma-200 indicator section #######
df_ma50, df_ma200 = clean_ma_data(
    ma_windows=['50', '180'], 
    ma_types=['sma', 'ema']
)


@app.callback(
    Output('ma-line-graph', 'figure'),
    [
        Input('ma-types', 'value'),
        Input('ma-window', 'value'),
        Input('ma-period', 'value')
    ]
)
def display_ma_series(types, window, period):
    if window == "50 days":
        df_ma = df_ma50
    else:
        df_ma = df_ma200
    if period == "Last Day":
        df_ma_cut = df_ma[:25]
    elif period == "Last Week":
        df_ma_cut = df_ma[:169]
    elif period == "Last Two Weeks":
        df_ma_cut = df_ma[:337]
    else:
        df_ma_cut = df_ma
    ma_types = []
    if "  Simple Moving Average (SMA)" in types:
        ma_types.append('SMA')
    if "  Exponential Moving Average (EMA)" in types:
        ma_types.append('EMA')
    ma_types.append('BTC price')
    fig = px.line(
        df_ma_cut,
        x='timestamp',
        y=ma_types,
        title="Moving Averages Index for X:BTC-USD indicator",
        labels={
            "value": "BTC Price",
            "timestamp": "Date"
        }
    )
    fig.layout.plot_bgcolor = COLORS['background']
    fig.layout.paper_bgcolor = COLORS['background']
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


@app.callback(
    Output("ma-collapse", "is_open"),
    [Input("ma-collapse-button", "n_clicks")],
    [State("ma-collapse", "is_open")],
)
def ma_toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


app.layout = render_layout(CRYPTO_ASSET_NAMES, df_fng)
server = app.server
if __name__ == '__main__':
    app.run_server()
