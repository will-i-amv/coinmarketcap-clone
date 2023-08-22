import datetime as dt
import functools as ft
import os

import pandas as pd
import requests


POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')


def get_assets():
    url = 'http://api.coincap.io/v2/assets?limit=10'
    try:
        response = requests.get(url)
        response_data = response.json()['data']
    except:
        response_data = {
            'id': [], 'rank': [], 'symbol': [], 'name': [], 'supply': [],
            'maxSupply': [], 'marketCapUsd': [], 'volumeUsd24Hr': [], 'priceUsd': [],
            'changePercent24Hr': [], 'vwap24Hr': [], 'explorer': [],
        }
    df = (
        pd
        .DataFrame(response_data)
        .astype({
            'rank': 'int64',
            'supply': 'float64',
            'maxSupply': 'float64',
            'marketCapUsd': 'float64',
            'volumeUsd24Hr': 'float64',
            'priceUsd': 'float64',
            'changePercent24Hr': 'float64',
            'vwap24Hr': 'float64',
        })
    )
    return df


def get_asset_history(start, end, currency, interval='d1'):
    unix_start = start.replace(tzinfo=dt.timezone.utc).timestamp() * 1000 # In miliseconds
    unix_end = end.replace(tzinfo=dt.timezone.utc).timestamp() * 1000 # In miliseconds
    url = (
        f"http://api.coincap.io/v2/assets/{currency}/history?" + 
        f"interval={interval}&start={unix_start}&end={unix_end}"
    )
    try:
        response = requests.get(url)
        response_data = response.json()['data']
    except:
        response_data = {'priceUsd': [], 'time': []}
    df_cleaned = (
        pd
        .DataFrame(response_data)
        .loc[:, ['priceUsd', 'time']]
        .astype({'priceUsd': 'float64', 'time': 'datetime64[ms]'})
        .rename(columns={'time': 'timestamp'})
    )
    return df_cleaned


def get_fear_greed_data():
    url = 'https://api.alternative.me/fng/?limit=365&date_format=us'
    try:
        response = requests.get(url)
        response_data = response.json()['data']
    except:
        response_data = {
            'value': [],
            'value_classification': [],
            'timestamp': [],
        }
    df = pd.DataFrame(response_data)
    df_clean = (
        df
        .loc[:, ['value', 'value_classification', 'timestamp']]
        .astype({'value': 'int64', 'timestamp': 'datetime64[ms]'})
        .sort_values(by=['timestamp'], ascending=False)
    )
    return df_clean


def get_rsi_data():
    url = (
        f'https://api.polygon.io/v1/indicators/rsi/X:BTCUSD' + 
        f'?timespan=hour&window=14&series_type=close&expand_underlying=false' + 
        f'&order=desc&limit=700&apiKey={POLYGON_API_KEY}'
    )
    try:
        response = requests.get(url)
        response_data = response.json()["results"]["values"]
    except:
        response_data = {'timestamp': [], 'value': []}
    df = (
        pd
        .DataFrame(response_data)
        .astype({'timestamp': 'datetime64[ms]'})
    )
    return df


def get_ma_data(window, ma_type):
    url = (
        f'https://api.polygon.io/v1/indicators/{ma_type}/X:BTCUSD?' +
        f'timespan=hour&window={window}&series_type=close&order=desc&limit=700' +
        f'&apiKey={POLYGON_API_KEY}'
    )
    try:
        response = requests.get(url)
        response_data = response.json()["results"]["values"]
    except:
        response_data = {'timestamp': [], 'value': []}
    df = pd.DataFrame(response_data).astype({'timestamp': 'datetime64[ms]'})
    return df


def clean_price_data(start, end, currencies):
    list_of_dfs = []
    for currency in currencies:
        df = get_asset_history(start, end, currency)
        df_cleaned = df.rename(columns={'priceUsd': f'{currency}'})
        list_of_dfs.append(df_cleaned)
    df_main_graph = (
        ft.reduce(
            lambda x, y: pd.merge(x, y, on=['timestamp'], how='outer'),
            list_of_dfs
        )
        .fillna(0)
        .sort_values(by=['timestamp'])
    )
    return df_main_graph


def clean_ma_data(ma_windows, ma_types):
    dfs_by_window = {}
    for ma_window in ma_windows:
        dfs_by_type = {}
        for ma_type in ma_types:
            dfs_by_type[ma_type] = get_ma_data(ma_window, ma_type)
        dfs_by_window[ma_window] = (
            pd
            .merge(dfs_by_type['sma'], dfs_by_type['ema'], on='timestamp', how='left')
            .rename(columns={'value_x': 'SMA', 'value_y': 'EMA'})
            .sort_values(by=['timestamp'])
        )
    df_ma50 = dfs_by_window['50']
    df_btc_price = get_asset_history(
        start=df_ma50["timestamp"].min(),
        end=df_ma50["timestamp"].max(),
        currency='bitcoin',
        interval='h1'
    )
    dfs_by_window_cleaned = {}
    for ma_window in ma_windows:
        dfs_by_window_cleaned[ma_window] = (
            dfs_by_window[ma_window]
            .merge(df_btc_price, on='timestamp', how='left')
            .rename(columns={'priceUsd': 'BTC price'})
        )
    return (dfs_by_window_cleaned['50'], dfs_by_window_cleaned['180'])
