import datetime

import services.coinbase as cb
from database.database import Database
import utils.utils

client = cb.get_client()
db = Database('mywow.db')

analysis_dir = utils.get_path_from_data_dir('analysis')

trading_pair = 'WIF-USD'
candles: dict[int, dict] = {
    12: {}, # December
    11: {}, # November
    10: {}  # October
}

for month_num in candles:
    start_date = datetime.datetime(year=2024, month=month_num, day=1)
    next_month = (start_date + datetime.timedelta(days=31)).replace(day=1)
    end_date = next_month - datetime.timedelta(days=1)

    candles[month_num] = cb.get_asset_candles(client, trading_pair, cb.Granularity.ONE_DAY, start_date, end_date)
    for candle in candles[month_num]:
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