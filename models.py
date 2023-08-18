import datetime as dt

from sqlalchemy import create_engine, Column, Date, String, Integer, Float
from sqlalchemy.orm import declarative_base, sessionmaker


engine = create_engine('sqlite:///exchange_rates_cache.db', echo=False)
base = declarative_base()
db_session = sessionmaker(bind=engine)
session = db_session()


class ExchangeRates(base):
    __tablename__ = "exchange_rates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)
    USD = Column(Float)
    PLN = Column(Float)
    EUR = Column(Float)
    GBP = Column(Float)
    CHF = Column(Float)

    def __init__(self, date, USD, PLN, EUR, GBP, CHF):
        self.date = date
        self.USD = USD
        self.PLN = PLN
        self.EUR = EUR
        self.GBP = GBP
        self.CHF = CHF


base.metadata.create_all(engine)


def save_exchange_rates(usd_price, pln_price, eur_price, gbp_price, chf_price):
    existing_record = (
        session
        .query(ExchangeRates)
        .filter(ExchangeRates.date == str(dt.date.today()))
        .first()
    )
    if not existing_record:
        data_record = ExchangeRates(
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
