import datetime

class MarketTrade:
    def __init__(self, init_data: dict):
        self.data = init_data

        self.trade_id: int = int(self.data['trade_id'])
        self.trading_pair: str = self.data['product_id']
        self.symbol: str = self.trading_pair.split('-')[0]

        self.price = float(self.data['price'])
        self.size = float(self.data['size'])

        self.side = self.data['side']
        self.total = self.price * self.size * (-1 if self.side == 'SELL' else 1)

        self.time = datetime.datetime.strptime(self.data['time'], '%Y-%m-%dT%H:%M:%SZ')

        self.bid = float(self.data.get('bid', 0))
        self.ask = float(self.data.get('ask', 0))
        self.exchange = self.data.get('exchange', 'unknown')

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

    def to_json(self) -> dict[str, str]:
        return {
            'trade_id': str(self.trade_id),
            'trading_pair': self.trading_pair,
            'price': str(self.price),
            'size': str(self.size),
            'time': self.view_iso_date(),
            'side': self.side,
            'bid': str(self.bid),
            'ask': str(self.ask),
            'exchange': self.exchange
        }