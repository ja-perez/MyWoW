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
                 symbol: str = '',
                 trading_pair: str = '',
                 start_date: Optional[datetime.datetime] = None,
                 end_date: Optional[datetime.datetime] = None,
                 start_price: float = 0,
                 end_price: float = 0,
                 buy_price: float = 0,
                 sell_price: float = 0,
                 close_price: float = 0):
        self.data = data

        self.symbol: str = symbol if symbol else ''
        self.trading_pair: str = trading_pair if trading_pair else ''

        self.start_date: datetime.datetime = start_date if start_date else datetime.datetime.today()
        self.end_date: datetime.datetime = end_date if end_date else datetime.datetime.today()

        self.start_price: float = start_price
        self.end_price: float = end_price
        self.close_price: float = close_price

        self.buy_price: float = buy_price
        self.sell_price: float = sell_price

        self.prediction_id: str = ""

        if self.data:
            try:
                self.verify_data()
            except MissingDataError:
                raise
            except InvalidDataError:
                raise
            except TypeError:
                raise

    def clear_data(self):
        self.symbol = ""
        self.trading_pair = ""
        self.start_date = None
        self.end_date = None
        self.start_price = 0
        self.end_price = 0
        self.buy_price = 0
        self.sell_price = 0
        self.close_price = 0
        self.prediction_id = ""

    def verify_data(self):
        try:
            # value verification
            self.trading_pair = self.trading_pair if self.trading_pair else self.data['trading_pair']
            if not self.trading_pair:
                raise MissingDataError

            self.symbol = self.symbol if self.symbol else self.data['symbol']
            if not self.symbol:
                raise MissingDataError

            if self.start_date.date() == self.end_date.date():
                if not self.data.get('start_date', None):
                    raise MissingDataError
                if not self.data.get('end_date', None):
                    raise MissingDataError

            self.start_price = self.start_price if self.start_price else self.data['start_price']
            if not self.start_price:
                raise MissingDataError

            self.end_price = self.end_price if self.end_price else self.data['end_price']
            if not self.end_price:
                raise MissingDataError

            self.buy_price = self.buy_price if self.buy_price else self.data['buy_price']
            if not self.buy_price:
                raise MissingDataError

            self.sell_price = self.sell_price if self.sell_price else self.data['sell_price']
            if not self.sell_price:
                raise MissingDataError

            self.close_price = self.close_price if self.close_price else self.data.get('close_price', 0)

           # type verification
            self.start_price = float(self.start_price)
            self.end_price = float(self.end_price)
            self.buy_price = float(self.buy_price)
            self.sell_price = float(self.sell_price)
            self.close_price = float(self.close_price)

            if type(self.data['start_date']) == str:
                self.start_date = datetime.datetime.strptime(self.data['start_date'], '%Y-%m-%d')
            else:
                self.start_date = self.data['start_date']

            if type(self.data['end_date']) == str:
                self.end_date = datetime.datetime.strptime(self.data['end_date'], '%Y-%m-%d')
            else:
                self.end_date = self.data['end_date']


            # validity of value verification
            if self.start_price <= 0 or self.end_price <= 0:
                raise InvalidDataError 
            if self.buy_price < 0 or self.sell_price < 0 or self.close_price < 0:
                raise InvalidDataError 
            if self.end_date < self.start_date:
                raise InvalidDataError 

            self.prediction_id = f"{self.symbol}-{self.start_date.month}{self.start_date.day}{self.end_date.month}{self.end_date.day}-{self.start_date.year}"
            if self.data.get('prediction_id', None) and self.data['prediction_id'] != self.prediction_id:
                raise InvalidDataError

        except KeyError:
            self.clear_data()
            raise MissingDataError
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
        data: list[str | float] = [
            self.prediction_id,
            self.symbol,
            self.trading_pair,
            self.view_start_date(),
            self.view_end_date(),
            self.start_price,
            self.end_price,
            self.buy_price,
            self.sell_price,
            self.close_price,
            ]
        return data

    def prediction_upload(self) -> list[str | float]:
        return [
            self.prediction_id,
            self.symbol,
            self.trading_pair,
            self.view_start_date(),
            self.view_end_date(),
            self.start_price,
            self.end_price,
            self.buy_price,
            self.sell_price,
        ]

    def result_upload(self) -> list[str | float]:
        data = self.prediction_upload()
        data.append(self.close_price)
        return data

    def to_json(self) -> dict[str, str | float]:
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