import datetime

import services.coinbase_services as cb
from database.database import Database
import utils.utils

client = cb.get_client()
db = Database('mywow.db')

trading_pair = 'BTC-USD'
candles: dict[str, dict] = {
    "2024-12-1": {}, # December
    "2024-11-1": {}, # November
    "2024-10-1": {}  # October
}

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

# fetch_candles(trading_pair, candles)


first_peak = [datetime.datetime(2025, 1, 16, 3, 10, 0), datetime.datetime(2025, 1, 16, 4, 15, 0)]
second_peak = [datetime.datetime(2025, 1, 15, 14, 0, 0), datetime.datetime(2025, 1, 15, 15, 0, 0)]
product_id = "BTC-USD"

def fetch_market_trades(product_id: str, start_time: datetime.datetime, end_time: datetime.datetime, get_candles: bool=False):
    start_unix = str(int(start_time.timestamp()))
    end_unix = str(int(end_time.timestamp()))
    market_trades = client.get_market_trades(product_id, 1000, start_unix, end_unix)
    for trade in market_trades['trades']:
        trade_id = trade['trade_id']
        trading_pair = trade['product_id']
        price = float(trade['price'])
        size = float(trade['size']) 
        time = trade['time']
        side = trade['side']
        bid = float(trade['bid']) if trade['bid'] else 0
        ask = float(trade['ask']) if trade['ask'] else 0
        exchange = trade['exchange'] if trade['exchange'] else 'unknown'

        insert_data = [
            trade_id,
            trading_pair,
            price,
            size,
            time,
            side,
            bid,
            ask,
            exchange
        ]
        db.insert_one(values=insert_data, table_name="market_trade")

    if get_candles:
        fetch_market_trade_candles(product_id, start_time, end_time)

def fetch_market_trade_candles(product_id: str, start_time: datetime.datetime, end_time: datetime.datetime):
    candles = cb.get_asset_candles(client, product_id, cb.Granularity.ONE_MINUTE, start_time, end_time)
    for candle in candles:
        start = int(candle['start'])
        date = datetime.datetime.fromtimestamp(start).isoformat()
        candle_open = float(candle['open'])
        high = float(candle['high'])
        low = float(candle['low'])
        close = float(candle['close'])
        volume = float(candle['volume'])
        symbol = product_id.split('-')[0]
        id = f"{symbol}-{start}"

        insert_data = [
            id,
            date,
            start,
            product_id,
            candle_open,
            high,
            low,
            close,
            volume
        ]
        db.insert_one(values=insert_data, table_name='market_candles')

# fetch_market_trades(product_id, first_peak[0], first_peak[1])
fetch_market_trade_candles(product_id, first_peak[0], first_peak[1])