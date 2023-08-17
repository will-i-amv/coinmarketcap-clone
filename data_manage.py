import datetime as dt
import functools as ft
import json
import os
import time

import pandas as pd
import requests
from sqlalchemy import create_engine, Column, String, Integer, Float
from sqlalchemy.orm import declarative_base, sessionmaker


POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')

engine = create_engine('sqlite:///exchange_rates_cache.db', echo=False)
base = declarative_base()
db_session = sessionmaker(bind=engine)
session = db_session()


class ExchangeRates(base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True)
    date = Column(String)
    USD = Column(Float)
    PLN = Column(Float)
    EUR = Column(Float)
    GBP = Column(Float)
    CHF = Column(Float)

    def __init__(self, id, date, USD, PLN, EUR, GBP, CHF):
        self.id = id
        self.date = date
        self.USD = USD
        self.PLN = PLN
        self.EUR = EUR
        self.GBP = GBP
        self.CHF = CHF


base.metadata.create_all(engine)


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


def get_price_data(start_time, end_time, currencies):
    list_of_dfs = []
    for currency in currencies:
        df = get_asset_history(start_time, end_time, currency)
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


def get_fear_greed_data():
    url = 'https://api.alternative.me/fng/?limit=365&date_format=us'
    try:
        response = requests.get(url)
        json_data = json.loads(response.text.encode('utf8'))
        df = pd.DataFrame(json_data["data"])
        df_clean = (
            df
            .loc[:, ['value', 'value_classification', 'timestamp']]
            .astype({'value': 'int64'})
        )
        df_clean_sampled = (
            df_clean
            .loc[[0, 1, 6, 29, 364], :]
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
    except:
        df_clean = pd.DataFrame({
            'value': [], 
            'value_classification': [], 
            'timestamp': []
        })
        df_clean_sampled = pd.DataFrame({'Value': [], 'Label': [], 'Time': []})
    return (df_clean, df_clean_sampled)


def get_rsi_data():
    url = (
        f'https://api.polygon.io/v1/indicators/rsi/X:BTCUSD' + 
        f'?timespan=hour&window=14&series_type=close&expand_underlying=false' + 
        f'&order=desc&limit=700&apiKey={POLYGON_API_KEY}'
    )
    try:
        response = requests.get(url)
        json_data = json.loads(response.text.encode('utf8'))
        df = (
            pd
            .DataFrame(json_data["results"]["values"])
            .astype({'timestamp': 'datetime64[ms]'})
        )
    except:
        df = pd.DataFrame({'timestamp': [], 'value': []})
    return df


def get_ma_data(window):
    base_url = lambda x: (
        f'https://api.polygon.io/v1/indicators/{x}/X:BTCUSD?' + 
        f'timespan=hour&window={window}&series_type=close&order=desc&limit=700' + 
        f'&apiKey={POLYGON_API_KEY}'
    )
    sma_url = base_url('sma')
    ema_url = base_url('ema')
    try:
        sma_response = requests.get(sma_url)
        ema_response = requests.get(ema_url)
        sma_json_data = sma_response.json()["results"]["values"]
        ema_json_data = ema_response.json()["results"]["values"]
        df_sma_ema = (
            pd
            .merge(
                pd.DataFrame(sma_json_data), 
                pd.DataFrame(ema_json_data), 
                on='timestamp', 
                how='left'
            )
            .astype({'timestamp': 'datetime64[ms]'})
            .sort_values(by=['timestamp'])
        )        
        
        start = df_sma_ema["timestamp"].min()
        end = df_sma_ema["timestamp"].max()
        df_btc_price = get_asset_history(start, end, currency='bitcoin', interval='h1')
        df = (
            df_sma_ema
            .merge(df_btc_price, on='timestamp', how='left')
            .astype({'timestamp': 'datetime64[ms]'})
            .rename(columns={
                'value_x': 'SMA',
                'value_y': 'EMA',
                'priceUsd': 'BTC price'
            })
        )
    except:
        df = pd.DataFrame()
    return df


def save_exchange_rates(usd_price, pln_price, eur_price, gbp_price, chf_price):
    existing_record = (
        session
        .query(ExchangeRates)
        .filter(ExchangeRates.date == str(dt.date.today()))
        .first()
    )
    if not existing_record:
        data_record = ExchangeRates(
            id=None,
            date=dt.date.today(),
            USD=usd_price,
            PLN=pln_price,
            EUR=eur_price,
            GBP=gbp_price,
            CHF=chf_price
        )
        session.add(data_record)
        session.commit()


def check_cache_database():
    date = "2023-03-25"
    usd_price = 1
    pln_price = 4.36
    eur_price = 0.93
    gbp_price = 0.82
    chf_price = 0.92
    existing_records = session.query(ExchangeRates).all()
    if not existing_records:
        data_record = ExchangeRates(
            id=None,
            date=date,
            USD=usd_price,
            PLN=pln_price,
            EUR=eur_price,
            GBP=gbp_price,
            CHF=chf_price
        )
        session.add(data_record)
        session.commit()


def get_from_cache_database(base_currency):
    check_cache_database()
    last_record = (
        session
        .query(ExchangeRates)
        .order_by(ExchangeRates.id.desc())
        .first()
    )
    if base_currency == "PLN":
        base = float(last_record.PLN)
    elif base_currency == "EUR":
        base = float(last_record.EUR)
    elif base_currency == "GBP":
        base = float(last_record.GBP)
    elif base_currency == "CHF":
        base = float(last_record.CHF)
    else:
        base = float(last_record.USD)
    usd_price = round(float(last_record.USD) / base, 2)
    pln_price = round(float(last_record.PLN) / base, 2)
    eur_price = round(float(last_record.EUR) / base, 2)
    gbp_price = round(float(last_record.GBP) / base, 2)
    chf_price = round(float(last_record.CHF) / base, 2)
    return last_record.date, usd_price, pln_price, eur_price, gbp_price, chf_price
