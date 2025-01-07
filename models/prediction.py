import datetime
# from utils.custom_exceptions import MissingDataError, InvalidDataError
class MissingDataError(Exception):
    """Raised when a prediction object is initialized missing key data"""
    pass

class InvalidDataError(Exception):
    """Raised when a prediction object is initialized with invalid data"""
    pass

class Prediction:
    def __init__(self, data: dict = None):
        self.symbol = ""
        self.trading_pair = ""

        self.start_price = 0
        self.end_price = 0
        self.buy_price = 0
        self.sell_price = 0
        self.actual_end_price = 0

        if data:
            try:
                self.verify_data(data)
            except MissingDataError:
                raise
            except InvalidDataError:
                raise
        else:
            self.new_data()

    def new_data(self):
        self.clear_data()
        # TODO: prompt user to input prediction data

    def clear_data(self):
        self.symbol = ""
        self.trading_pair = ""
        self.start_price = 0
        self.end_price = 0
        self.buy_price = 0
        self.sell_price = 0
        self.actual_end_price = 0

    def verify_data(self, data: dict):
        try:
            # value verification
            trading_pair = data.get(trading_pair, None)
            if "trading_pair" not in data:
                raise MissingDataError
            if "symbol" not in data:
                raise MissingDataError
            if "start_date" not in data:
                raise MissingDataError
            if "end_date" not in data:
                raise MissingDataError
            if "buy_price" not in data:
                raise MissingDataError
            if "sell_price" not in data:
                raise MissingDataError
            
            # type verification
            self.start_price = float(data["start_price"])
            self.end_price = float(data["end_price"])
            self.buy_price = float(data["buy_price"])
            self.sell_price = float(data["sell_price"])

            self.start_date = datetime.datetime.strptime(data["start_date"], "%Y-%m-%d")
            self.end_date = datetime.datetime.strptime(data["end_date"], "%Y-%m-%d")

            # validity of value verification
            if self.start_price <= 0 or self.end_price <= 0:
                raise InvalidDataError 
            if self.buy_price < 0 or self.sell_price < 0 or self.actual_end_price < 0:
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

        self.actual_end_price = 0