import datetime
from typing import Optional

class MissingDataError(Exception):
    """Raised when a prediction object is initialized missing key data"""
    pass

class InvalidDataError(Exception):
    """Raised when a prediction object is initialized with invalid data"""
    pass

class Prediction:
    def __init__(self,
                 data: Optional[dict] = None,
                 symbol: Optional[str] = None,
                 trading_pair: Optional[str] = None,
                 start_date: Optional[datetime.datetime] = None,
                 end_date: Optional[datetime.datetime] = None,
                 start_price: Optional[float] = None,
                 end_price: Optional[float] = None,
                 buy_price: Optional[float] = None,
                 sell_price: Optional[float] = None,
                 close_price: Optional[float] = None):
        self.data = data if data else {}
        self.symbol = symbol if symbol else self.data.get('symbol', '')
        self.trading_pair = trading_pair if trading_pair else self.data.get('trading_pair', '')

        self.start_date = start_date if start_date else self.data.get('start_date', None)
        self.end_date = end_date if end_date else self.data.get('end_date', None)

        self.start_price = start_price if start_price else self.data.get('start_price', 0)
        self.end_price = end_price if end_price else self.data.get('end_price', 0)
        self.close_price = close_price if close_price else self.data.get('close_price', 0)

        self.buy_price = buy_price if buy_price else self.data.get('buy_price', 0)
        self.sell_price = sell_price if sell_price else self.data.get('buy_price', 0)

        self.prediction_id = ""

        if data:
            try:
                self.verify_data(data)
            except MissingDataError:
                raise
            except InvalidDataError:
                raise
            except TypeError:
                raise

    def clear_data(self):
        self.symbol = ""
        self.trading_pair = ""
        self.start_price = 0
        self.end_price = 0
        self.buy_price = 0
        self.sell_price = 0
        self.close_price = 0

    def verify_data(self, data: dict):
        try:
            # value verification
            self.trading_pair = self.trading_pair if self.trading_pair else data.get('trading_pair', None)
            if not self.trading_pair:
                raise MissingDataError

            self.symbol = self.symbol if self.symbol else data.get('symbol', None)
            if not self.symbol:
                raise MissingDataError

            self.start_date = self.start_date if self.start_date else data.get('start_date', None)
            if not self.start_date:
                raise MissingDataError

            self.end_date = self.end_date if self.end_date else data.get('end_date', None)
            if not self.end_date:
                raise MissingDataError

            self.start_price = self.start_price if self.start_price else data.get('start_price', None)
            if not self.start_price:
                raise MissingDataError

            self.end_price = self.end_price if self.end_price else data.get('end_price', None)
            if not self.end_price:
                raise MissingDataError

            self.buy_price = self.buy_price if self.buy_price else data.get('buy_price', None)
            if not self.buy_price:
                raise MissingDataError

            self.sell_price = self.sell_price if self.sell_price else data.get('sell_price', None)
            if not self.sell_price:
                raise MissingDataError

            self.close_price = self.close_price if self.close_price else data.get('close_price', 0)

           # type verification
            self.start_price = float(self.start_price)
            self.end_price = float(self.end_price)
            self.buy_price = float(self.buy_price)
            self.sell_price = float(self.sell_price)
            self.close_price = float(self.close_price)

            if type(self.start_date) == str:
                self.start_date = datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
            if type(self.end_date) == str:
                self.end_date = datetime.datetime.strptime(self.end_date, "%Y-%m-%d")

            # validity of value verification
            if self.start_price <= 0 or self.end_price <= 0:
                raise InvalidDataError 
            if self.buy_price < 0 or self.sell_price < 0 or self.close_price < 0:
                raise InvalidDataError 
            if self.end_date < self.start_date:
                raise InvalidDataError 

            self.prediction_id = f"{self.symbol}-{self.start_date.month}{self.start_date.day}{self.end_date.month}{self.end_date.day}-{self.start_date.year}"
            if data.get('prediction_id', None) and data['prediction_id'] != self.prediction_id:
                raise InvalidDataError

        except MissingDataError:
            self.clear_data()
            raise
        except TypeError:
            self.clear_data()
            raise
        except InvalidDataError:
            self.clear_data()
            raise

    def view_start_date(self) -> str:
        if type(self.start_date) == datetime.datetime:
            return self.start_date.strftime("%Y-%m-%d")
        return "XXXX-XX-XX"

    def view_end_date(self) -> str:
        if type(self.end_date) == datetime.datetime:
            return self.end_date.strftime("%Y-%m-%d")
        return "XXXX-XX-XX"

    def get_values(self) -> list[str | float]:
        return [
            self.prediction_id,
            self.symbol,
            self.trading_pair,
            self.view_start_date(),
            self.view_end_date(),
            self.start_price,
            self.end_price,
            self.buy_price,
            self.end_price,
        ]

    def to_json(self):
        return {
            'symbol': self.symbol,
            'trading_pair': self.trading_pair,
            'start_date': self.view_start_date(),
            'end_date': self.view_start_date(),
            'start_price': str(self.start_price),
            'end_price': str(self.end_price),
            'buy_price': str(self.buy_price),
            'sell_price': str(self.sell_price),
            'close_price': str(self.close_price)
        }