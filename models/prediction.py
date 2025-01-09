import datetime

class MissingDataError(Exception):
    """Raised when a prediction object is initialized missing key data"""
    pass

class InvalidDataError(Exception):
    """Raised when a prediction object is initialized with invalid data"""
    pass

class Prediction:
    def __init__(self,
                 symbol: str = None,
                 trading_pair: str = None,
                 start_date: datetime.datetime = None,
                 end_date: datetime.datetime = None,
                 start_price: float = None,
                 end_price: float = None,
                 buy_price: float = None,
                 sell_price: float = None,
                 close_price: float = None,
                 data: dict = None):

        self.symbol = symbol
        self.trading_pair = trading_pair

        self.start_date = start_date
        self.end_date = end_date

        self.start_price = start_price
        self.end_price = end_price
        self.close_price = close_price

        self.buy_price = buy_price
        self.sell_price = sell_price

        if data:
            try:
                self.verify_data(data)
            except MissingDataError:
                raise
            except InvalidDataError:
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

           # type verification
            self.start_price = float(self.start_price)
            self.end_price = float(self.end_price)
            self.buy_price = float(self.buy_price)
            self.sell_price = float(self.sell_price)

            self.start_date = datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
            self.end_date = datetime.datetime.strptime(self.end_date, "%Y-%m-%d")

            # validity of value verification
            if self.start_price <= 0 or self.end_price <= 0:
                raise InvalidDataError 
            if self.buy_price < 0 or self.sell_price < 0 or self.close_price < 0:
                raise InvalidDataError 
            if self.end_date < self.start_date:
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

    def submit(self):
        return [
            f"{self.symbol}",
            self.symbol,
            self.trading_pair,
            datetime.datetime.strftime(self.start_date, "%Y-%m-%d"),
            datetime.datetime.strftime(self.end_date, "%Y-%m-%d"),
            self.start_price,
            self.end_price,
            self.buy_price,
            self.end_price,
        ]

class Result(Prediction):
    def __init__(self, data: dict = None):
        super.__init__(data)

        self.close_price = 0