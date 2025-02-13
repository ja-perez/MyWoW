import datetime

class Candle:
    def __init__(self, init_data: dict):
        self.data = init_data

        self.start: int = int(self.data['start'])
        self.time: datetime.datetime = datetime.datetime.fromtimestamp(self.start).astimezone()
        self.date: datetime.datetime = self.time

        self.trading_pair: str = self.data['trading_pair']
        self.symbol: str = self.trading_pair.split('-')[0]
        self.granularity: str = self.data['granularity']

        self.open_price: float = float(self.data['open'])
        self.high_price: float = float(self.data['high'])
        self.low_price: float = float(self.data['low'])
        self.close_price: float = float(self.data['close'])
        self.volume: float = float(self.data['volume'])

        self.range_high: float = 0
        self.range_low: float = 0

        self.candle_id = f"{self.symbol}-{self.start}"

    def view_date(self) -> str:
        if type(self.time) == datetime.datetime:
            return self.time.strftime("%Y-%m-%d")
        return "XXXX-XX-XX"

    def view_iso_date(self) -> str:
        if type(self.time) == datetime.datetime:
            return self.time.isoformat()
        return "XXXX-XX-XXTXX:XX:XXZ"

    def get_values(self) -> list[str | float]:
        return [
            self.candle_id,
            self.view_iso_date(),
            self.start,
            self.trading_pair,
            self.open_price,
            self.high_price,
            self.low_price,
            self.close_price,
            self.volume,
            self.granularity
        ]

    def to_json(self) -> dict[str, str]:
        return {
            'candle_id': self.candle_id,
            'time': self.view_iso_date(),
            'start': str(self.start),
            'trading_pair': self.trading_pair,
            'open': str(self.open_price),
            'high': str(self.high_price),
            'low': str(self.low_price),
            'close': str(self.close_price),
            'volume': str(self.volume),
            'granularity': self.granularity
        }

    def to_dict(self) -> dict:
        return {
            'candle_id': self.candle_id,
            'time': self.time,
            'start': self.start,
            'trading_pair': self.trading_pair,
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume,
            'granularity': self.granularity
        }