import datetime
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


def get_names():
    url = 'http://api.coincap.io/v2/assets?limit=10'
    try:
        response = requests.get(url)
        json_data = json.loads(response.text.encode('utf8'))
        crypto_names = pd.DataFrame(json_data["data"]).loc[:, 'id'].to_list()
    except:
        crypto_names = []
    return crypto_names


def get_price_data(start_time, end_time, currencies):
    unix_start_time = time.mktime(start_time.timetuple()) * 1000
    unix_end_time = time.mktime(end_time.timetuple()) * 1000
    try:
        list_of_dfs = []
        for currency in currencies:
            url = (
                f"http://api.coincap.io/v2/assets/{currency}/history?interval=d1" +
                f"&start={unix_start_time}&end={unix_end_time}"
            )
            response = requests.get(url).text.encode('utf8')
            df = pd.DataFrame(json.loads(response)["data"])
            df_cleaned = (
                df
                .assign(date=lambda x: x['date'].str.replace('T00:00:00.000Z', ''))
                .astype({'priceUsd': 'float64', 'date': 'datetime64[ns]'})
                .rename(columns={'priceUsd': f'{currency}'})
                .drop(labels=['time'], axis=1)
            )
            list_of_dfs.append(df_cleaned)
        df_main_graph = (
            ft.reduce(
                lambda x, y: pd.merge(x, y, on=['date'], how='outer'),
                list_of_dfs
            )
            .fillna(0)
            .sort_values(by=['date'])
        )
    except:
        df_main_graph = pd.DataFrame({
            label: []
            for label in ['date'] + currencies
        })
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


def prepare_btc_price_for_ma_indicator(df_ma50):
    start_time = float(df_ma50["timestamp"].min())
    end_time = float(df_ma50["timestamp"].max())
    url_price_btc = (
        f"http://api.coincap.io/v2/assets/bitcoin/history" +
        f"?interval=h1&start={start_time}&end={end_time}"
    )
    try:
        response = requests.request("GET", url_price_btc)
        json_data = json.loads(response.text.encode('utf8'))
        data = json_data["data"]
        df_btc_price = pd.DataFrame(data)
        df_btc_price = df_btc_price.rename(columns={"time": "timestamp"})
        df_btc_price['priceUsd'] = df_btc_price['priceUsd'].astype(float)
    except:
        df_btc_price = pd.DataFrame()
    return df_btc_price


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
        sma_json_data = json.loads(sma_response.text.encode('utf8'))
        ema_json_data = json.loads(ema_response.text.encode('utf8'))
        df_sma = pd.DataFrame(sma_json_data["results"]["values"])
        df_ema = pd.DataFrame(ema_json_data["results"]["values"])
        df_sma_ema = pd.merge(df_sma, df_ema, on='timestamp', how='left')
        df_btc_price = prepare_btc_price_for_ma_indicator(df_sma_ema)
        df = (
            df_sma_ema
            .merge(df_btc_price, on='timestamp', how='left')
            .astype({'timestamp': 'datetime64[ns]'})
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
        .filter(ExchangeRates.date == str(datetime.date.today()))
        .first()
    )
    if not existing_record:
        data_record = ExchangeRates(
            id=None,
            date=datetime.date.today(),
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
