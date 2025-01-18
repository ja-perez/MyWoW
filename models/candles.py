import datetime
from typing import Optional

class Candle:
    def __init__(self, init_data: dict):
        self.data = init_data

        self.start = int(self.data['start'])
        self.date = datetime.datetime.strptime(self.data['date'], '%Y-%m-%d')
        self.time = datetime.datetime.fromtimestamp(self.start)

        self.trading_pair: str = self.data['trading_pair']
        self.symbol: str = self.trading_pair.split('-')[0]

        self.open = float(self.data['open'])
        self.high = float(self.data['high'])
        self.low = float(self.data['low'])
        self.close = float(self.data['close'])
        self.volume = float(self.data['volume'])

        self.candle_id = f"{self.symbol}-{self.start}"

    def view_date(self) -> str:
        if type(self.date) == datetime.datetime:
            return self.date.strftime("%Y-%m-%d")
        return "XXXX-XX-XX"

    def view_time(self) -> str:
        if type(self.time) == datetime.datetime:
            return self.time.isoformat()
        return "XXXX-XX-XXTXX:XX:XXZ"

    def get_values(self) -> list[str | float]:
        return [
            self.candle_id,
            self.view_date(),
            self.start,
            self.trading_pair,
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
        ]

    def to_json(self) -> dict[str, str]:
        return {
            'candle_id': self.candle_id,
            'date': self.view_date(),
            'start': str(self.start),
            'trading_pair': self.trading_pair,
            'open': str(self.open),
            'high': str(self.high),
            'low': str(self.low),
            'close': str(self.close),
            'volume': str(self.volume)
        }