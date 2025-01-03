# from utils.custom_exceptions import MissingDataError, InvalidDataError
class MissingDataError(Exception):
    """Raised when a prediction object is initialized missing key data"""
    pass

class InvalidDataError(Exception):
    """Raised when a prediction object is initialized with invalid data"""
    pass

class Prediction:
    def __init__(self, data: dict = None):
        self.data = {}

        if data and self.verify_data(data):
            self.data = data

    @staticmethod
    def verify_data(data):
        try:
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
            if "sell_rpice" not in data:
                raise MissingDataError
            return True
        except MissingDataError:
            return False