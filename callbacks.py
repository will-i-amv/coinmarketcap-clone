import datetime as dt
import json
from dateutil import parser

import pandas as pd
import plotly.express as px
import requests
from dash import Input, Output, State
from forex_python.converter import CurrencyRates

from app import app
from common import CURRENCY_SYMBOLS, COLORS
from data_manage import (
    get_assets, get_price_data, get_fear_greed_data, get_rsi_data, get_ma_data,
    save_exchange_rates, get_from_cache_database
)


##### Main crypto graph section #####
crypto_assets = get_assets()
CRYPTO_CURRENCIES = crypto_assets.loc[:, 'id'].to_list()
default_start_time = dt.datetime(2015, 1, 1)
default_end_time = dt.datetime.now()
df_main_graph = get_price_data(
    default_start_time,
    default_end_time,
    CRYPTO_CURRENCIES
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
    try:
        currency_rates = CurrencyRates()
        usd_rate = currency_rates.get_rate('USD', base_currency)
    except:
        date, usd_price, pln_price, eur_price, gbp_price, chf_price = get_from_cache_database(
            base_currency
        )
        usd_rate = 1/usd_price
    df = (
        df_main_graph
        .loc[lambda x: x['timestamp'].between(start_time, end_time)]
        .set_index('timestamp')
        .multiply(usd_rate)
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


alert_message = True


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
    try:
        currency_rates = CurrencyRates()
        usd_price = round(currency_rates.get_rate(base_currency, 'USD'), 2)
        pln_price = round(currency_rates.get_rate(base_currency, 'PLN'), 2)
        eur_price = round(currency_rates.get_rate(base_currency, 'EUR'), 2)
        gbp_price = round(currency_rates.get_rate(base_currency, 'GBP'), 2)
        chf_price = round(currency_rates.get_rate(base_currency, 'CHF'), 2)
        if base_currency == "USD":
            save_exchange_rates(
                usd_price,
                pln_price,
                eur_price,
                gbp_price,
                chf_price
            )
        alert_message = "Everything ok"
        color = "info"
        is_open = False
    except:
        date, usd_price, pln_price, eur_price, gbp_price, chf_price = get_from_cache_database(
            base_currency
        )
        alert_message = f"Warning! Currency rates are out of date! (retrieved of {date}). Be careful."
        color = "primary"
        is_open = True
    return usd_price, pln_price, eur_price, gbp_price, chf_price, alert_message, color, is_open


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
    try:
        currency_rates = CurrencyRates()
        usd_rate = currency_rates.get_rate('USD', base_currency)
    except:
        date, usd_price, pln_price, eur_price, gbp_price, chf_price = get_from_cache_database(
            base_currency
        )
        usd_rate = 1/usd_price
    curr_symbol = CURRENCY_SYMBOLS[base_currency]
    df_cleaned = (
        crypto_assets
        .assign(
            priceUsd=lambda x: x['priceUsd'] * usd_rate,
            marketCapUsd=lambda x: x['marketCapUsd'] * usd_rate,
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
df_fng, df_short_fng = get_fear_greed_data()


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
    fig.update_xaxes(showgrid=False, zeroline=False, autorange="reversed")
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
df_ma50 = get_ma_data(window='50')
df_ma200 = get_ma_data(window='180')


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
