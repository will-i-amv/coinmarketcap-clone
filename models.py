import pandas as pd
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


def get_exchange_rates(date):
    query = (
        session
        .query(ExchangeRates)
        .filter(ExchangeRates.date == date)
        .order_by(ExchangeRates.id.desc())
        .limit(1)
    )
    df = pd.read_sql(con=engine, sql=query.statement)
    return df


def save_exchange_rates(record):
    obj = ExchangeRates(**record)
    session.add(obj)
    session.commit()
