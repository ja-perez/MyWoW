import datetime
import pandas as pd # type: ignore
from coinbase.rest import RESTClient # type: ignore
from math import ceil

import services.coinbase_services as cb
from database.database import Database
from database.db_setup import MyWoWDatabase
from models import Candle, MarketTrade

def fetch_candles(trading_pair: str, candles: dict[str, dict]):
    for start_date_string in candles:
        start_date = datetime.datetime.strptime(start_date_string, "%Y-%m-%d")
        next_month = (start_date + datetime.timedelta(days=31)).replace(day=1)
        end_date: datetime.datetime = next_month - datetime.timedelta(days=1)

        candles[start_date_string] = cb.get_asset_candles(client, trading_pair, cb.Granularity.ONE_DAY, start_date, end_date)
        for candle in candles[start_date_string]:
            start = int(candle['start'])
            date = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d')
            candle_open = float(candle['open'])
            high = float(candle['high'])
            low = float(candle['low'])
            close = float(candle['close'])
            volume = float(candle['volume'])
            symbol = trading_pair.split('-')[0]
            id = f"{symbol}-{start}"

            insert_data = [
                id,
                date,
                start,
                trading_pair,
                candle_open,
                high,
                low,
                close,
                volume
            ]
            db.insert_one(values=insert_data, table_name='candles')

#######################################################################################################################

def fetch_and_upload_data(client: RESTClient, trading_pair: str, start_time: datetime.datetime, end_time: datetime.datetime):
    # fetch all market trades between time range and upload to db
    market_trades = cb.fetch_market_trades(client, trading_pair, start_time, end_time, cb.CANDLES_LIMIT_MAX)
    for market_trade_data in market_trades:
        market_trade = MarketTrade(market_trade_data)
        dbms.add_item(table_name='market_trade', values=market_trade.get_values())
    
    # fetch candles between same time range as market trades and upload to db
    candles = cb.fetch_market_trade_candles(client, trading_pair, start_time, end_time, cb.CANDLES_LIMIT_MAX)
    for candle_data in candles:
        candle = Candle(candle_data)
        dbms.add_item(table_name='market_candles', values=candle.get_values(market_trade_candle=True))

client = cb.get_client()
db = Database('mywow.db')
dbms = MyWoWDatabase('mywow.db')

trading_pair = 'BTC-USD'
start = datetime.datetime.strptime('2025-02-05T12:00:0.0Z', '%Y-%m-%dT%H:%M:%S.%fZ')
end = datetime.datetime.strptime('2025-02-05T16:00:0.0Z', '%Y-%m-%dT%H:%M:%S.%fZ')

time_delta = end - start
time_delta_in_seconds = ceil(time_delta.seconds + time_delta.days * 24 * 3600 + time_delta.microseconds / 1e6)

def main():
    res = dbms.get_items(
        table_name='market_candles', 
        where_statement=f"WHERE trading_pair='{trading_pair}'")
    market_candles = [Candle(trade) for trade in res]
    df_candles = pd.DataFrame(data=[trade.to_dict() for trade in market_candles])
    df_candles['time'] = df_candles['date']
    df_candles['date'] = pd.Series(data=[date.date() for date in df_candles['date']])
    df_candles = df_candles[(df_candles['date'] >= start.date()) & (df_candles['date'] <= end.date())]
    print(df_candles.head())
    print(df_candles.dtypes)

if __name__=='__main__':
    main()