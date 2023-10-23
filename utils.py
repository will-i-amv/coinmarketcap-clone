import datetime as dt
import functools as ft

import numpy as np
import pandas as pd

import api
import models


def clean_price_data(start, end, currencies):
    list_of_dfs = []
    for currency in currencies:
        df = api.get_asset_history(start, end, currency)
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
            dfs_by_type[ma_type] = api.get_ma_data(ma_window, ma_type)
        dfs_by_window[ma_window] = (
            pd
            .merge(dfs_by_type['sma'], dfs_by_type['ema'], on='timestamp', how='left')
            .rename(columns={'value_x': 'SMA', 'value_y': 'EMA'})
            .sort_values(by=['timestamp'])
        )
    df_ma50 = dfs_by_window['50']
    start_datetime = df_ma50["timestamp"].min() 
    end_datetime = df_ma50["timestamp"].max()
    if (start_datetime is np.nan) and (end_datetime is np.nan):
        return tuple(dfs_by_window.values())
    else:
        df_btc_price = api.get_asset_history(
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
        return tuple(dfs_by_window_cleaned.values())


def clean_exchange_rates(date, currency_names):
    df = models.get_exchange_rates(date)
    if df.empty:
        df = api.get_exchange_rates()
        record = (
            df
            .loc[:, currency_names]
            .assign(date=date)
            .to_dict('records')[0]
        )
        models.save_exchange_rates(record)
    rates = df.loc[:, currency_names].to_dict('records')[0]
    return rates


def resample_df_fng(df):
    today = df['timestamp'].max()
    selected_dates = [
        today - dt.timedelta(days=day)
        for day in [0, 1, 6, 29, 364]
    ]
    df_sampled = (
        df
        .loc[lambda x: x['timestamp'].isin(selected_dates)]
        .assign(Time=[
            "Now",
            "Yesterday",
            "Week ago",
            "Month ago",
            "Year ago"
        ])
        .rename(columns={'value': 'Value', 'value_classification': 'Label'})
        .drop(labels=['timestamp'], axis=1)
        .reset_index(drop=True)
    )
    return df_sampled
