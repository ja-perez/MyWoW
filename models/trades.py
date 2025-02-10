import datetime

class MissingDataError(Exception):
    """Raised when a prediction object is initialized missing key data"""
    pass

class MarketTrade:
    def __init__(self, data: dict):
        self.init_data = data

        self.trade_id: str = self.init_data['trade_id']
        self.trading_pair: str = self.init_data.get('product_id', self.init_data.get('trading_pair', None))
        if not self.trading_pair:
            raise MissingDataError
        self.symbol: str = self.trading_pair.split('-')[0]

        self.price = float(self.init_data['price'])
        self.size = float(self.init_data['size'])

        self.side = self.init_data['side']
        self.total = self.price * self.size * (-1 if self.side == 'SELL' else 1)

        self.time = self.init_data['time'] if type(self.init_data['time']) == datetime.datetime else datetime.datetime.fromisoformat(self.init_data['time']).astimezone()

        self.bid = float(self.init_data['bid'] if self.init_data['bid'] else 0)
        self.ask = float(self.init_data['ask'] if self.init_data['ask'] else 0)
        self.exchange = self.init_data['exchange'] if self.init_data['exchange'] else 'UKNOWN_EXCHANGE'

    def view_date(self) -> str:
        return self.time.strftime('%Y-%m-%d')

    def view_datetime(self) -> str:
        return self.time.strftime('%Y-%m-%dT%H:%M:%S')

    def view_iso_date(self) -> str:
        return self.time.isoformat()

    def get_values(self) -> list[str | float]:
        return [
            self.trade_id,
            self.trading_pair,
            self.price,
            self.size,
            self.view_iso_date(),
            self.side,
            self.bid,
            self.ask,
            self.exchange
        ]

    def to_json(self) -> dict:
        return {
            'trade_id': self.trade_id,
            'trading_pair': self.trading_pair,
            'price': str(self.price),
            'size': str(self.size),
            'time': self.view_iso_date(),
            'side': self.side,
            'bid': str(self.bid),
            'ask': str(self.ask),
            'exchange': self.exchange
        }

    def to_dict(self) -> dict:
        return {
            'trade_id': self.trade_id,
            'trading_pair': self.trading_pair,
            'price': self.price,
            'size': self.size,
            'time': self.time,
            'side': self.side,
            'bid': self.bid,
            'ask': self.ask,
            'exchange': self.exchange
        }