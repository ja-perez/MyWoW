import os

from database.database import Database, InvalidTableNameError, InvalidValuesError, DuplicateInsertError
from models.prediction import Prediction
from models.candles import Candle

class DBMSConstructionError(Exception):
    """Raised when a database management system object cannot be created"""
    pass

class TableConstructionError(Exception):
    """Raised when a table cannot be created in a database"""
    pass

class InvalidLocalStorageError(Exception):
    """Raised when data found in local storage is invalid due to formatting or configuration"""
    pass

class MyWoWDatabase:
    data_dir = os.path.join(os.getcwd(), 'data')
    candles_dir = os.path.join(data_dir, 'candles')

    local_predictions_path = os.path.join(data_dir, 'local_predictions.csv')
    local_results_path = os.path.join(data_dir, 'local_results.csv')

    local_predictions_header = ['symbol', 'trading_pair', 'start_date', 'end_date', 'start_price', 'end_price', 'buy_price', 'sell_price']
    local_results_header = local_predictions_header + ['close_price']

    table_definitions = {
        'predictions': {
            "prediction_id": "TEXT PRIMARY KEY UNIQUE",
            "symbol": "TEXT",
            "trading_pair": "TEXT",
            "start_date": "DATE",
            "end_date": "DATE",
            "start_price": "REAL",
            "end_price": "REAL",
            "buy_price": "REAL",
            "sell_price": "REAL",
            },
        'results': {
            "prediction_id": "TEXT PRIMARY KEY UNIQUE",
            "symbol": "TEXT",
            "trading_pair": "TEXT",
            "start_date": "DATE",
            "end_date": "DATE",
            "start_price": "REAL",
            "end_price": "REAL",
            "buy_price": "REAL",
            "sell_price": "REAL",
            "close_price": "REAL",
            },
        'candles': {
            "candle_id": "TEXT PRIMARY KEY UNIQUE",
            "date": "DATE",
            "start": "INT",
            "trading_pair": "TEXT",
            "open": "REAL",
            "high": "REAL",
            "low": "REAL",
            "close": "REAL",
            "volume": "REAL",
            },
        'market_trade': {
            "trade_id": "TEXT PRIMARY KEY UNIQUE",
            "trading_pair": "TEXT",
            "price": "REAL",
            "size": "REAL",
            "time": "DATETIME",
            "side": "TEXT",
            "bid": "REAL",
            "ask": "REAL",
            "exchange": "TEXT"
            },
        'market_candles': {
            "candle_id": "TEXT PRIMARY KEY UNIQUE",
            "time": "DATETIME",
            "start": "INT",
            "trading_pair": "TEXT",
            "open": "REAL",
            "high": "REAL",
            "low": "REAL",
            "close": "REAL",
            "volume": "REAL",
            }
    }

    def __init__(self, db_name: str = "mywow.db"):
        self.db_name = db_name
        self.db = Database(db_name)

        self.setup_local_storage()
        self.setup_database()

        self.upload_local_predictions()
        self.upload_local_results()

    def setup_database(self):
        try:
            self.predictions_setup()
        except TableConstructionError:
            raise DBMSConstructionError

        try:
            self.results_setup()
        except TableConstructionError:
            raise DBMSConstructionError

        try:
            self.candles_setup()
        except TableConstructionError:
            raise DBMSConstructionError

        try:
            self.market_trades_setup()
        except TableConstructionError:
            raise DBMSConstructionError

    def setup_local_storage(self):
        # directories
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        if not os.path.exists(self.candles_dir):
            os.mkdir(self.candles_dir) 

        # predictions
        if os.path.exists(self.local_predictions_path):
            with open(self.local_predictions_path, 'r') as f:
                local_header = f.readline().strip('\n')
                if local_header != ','.join(self.local_predictions_header):
                    # Need to raise error as we have to assume all data in file follows the format of the incorrect header
                    raise InvalidLocalStorageError 
        else:
            with open(self.local_predictions_path, 'x') as f:
                f.write(','.join(self.local_predictions_header))

        # results
        if os.path.exists(self.local_results_path):
            with open(self.local_results_path, 'r') as f:
                local_header = f.readline().strip('\n')
                if local_header != ','.join(self.local_results_header):
                    # Need to raise error as we have to assume all data in file follows the format of the incorrect header
                    raise InvalidLocalStorageError 
        else:
            with open(self.local_results_path, 'x') as f:
                f.write(','.join(self.local_results_header))

    def upload_local_predictions(self):
        # predictions
        with open(self.local_predictions_path, 'r') as f:
            _header = f.readline()
            rows = [line.strip('\n').split(',') for line in f.readlines()]
            predictions = []
            for values in rows:
                header_to_value = {
                    self.local_predictions_header[i]: value for i, value in enumerate(values)
                }
                predictions.append(Prediction(header_to_value))
            for prediction in predictions:
                try:
                    self.db.insert_one(table_name='predictions', values=prediction.prediction_upload())
                except DuplicateInsertError:
                    continue
                except InvalidValuesError:
                    continue

    def upload_local_results(self):
        # results
        with open(self.local_results_path, 'r') as f:
            _header = f.readline()
            rows = [line.strip('\n').split(',') for line in f.readlines()]
            results = []
            for values in rows:
                header_to_value = {
                    self.local_results_header[i]: value for i, value in enumerate(values)
                }
                results.append(Prediction(header_to_value))
            for result in results:
                try:
                    self.db.insert_one(table_name='results', values=result.result_upload())
                except DuplicateInsertError:
                    continue
                except InvalidValuesError:
                    continue

    def create_table(self, table_name: str, table_definition: dict[str, str]):
        try:
            if self.db.table_exists(table_name):
                existing_table_def = self.db.get_table_def(table_name)
                if existing_table_def == table_definition:
                    return
                else:
                    raise TableConstructionError
            self.db.create_table(table_name=table_name, values=table_definition)
        except InvalidTableNameError:
            raise TableConstructionError
        except InvalidValuesError:
            raise TableConstructionError
        except TableConstructionError:
            raise 

    def predictions_setup(self):
        # Prediction ID:
        #   [symbol]-[start_month][start_day][end_month][end_day]-[start_year]
        predictions_def = {
            "prediction_id": "TEXT PRIMARY KEY UNIQUE",
            "symbol": "TEXT",
            "trading_pair": "TEXT",
            "start_date": "DATE",
            "end_date": "DATE",
            "start_price": "REAL",
            "end_price": "REAL",
            "buy_price": "REAL",
            "sell_price": "REAL",
        }
        try:
            self.create_table(table_name='predictions', table_definition=self.table_definitions['predictions'])
        except InvalidTableNameError as ITE:
            raise TableConstructionError
        except InvalidValuesError:
            raise TableConstructionError
        except TableConstructionError:
            raise

    def results_setup(self):
        # Prediction ID:
        #   [symbol]-[start_month][start_day][end_month][end_day]-[start_year]
        results_def = {
            "prediction_id": "TEXT PRIMARY KEY UNIQUE",
            "symbol": "TEXT",
            "trading_pair": "TEXT",
            "start_date": "DATE",
            "end_date": "DATE",
            "start_price": "REAL",
            "end_price": "REAL",
            "buy_price": "REAL",
            "sell_price": "REAL",
            "close_price": "REAL",
        }
        try:
            self.create_table(table_name='results', table_definition=self.table_definitions['results'])
        except InvalidTableNameError:
            raise TableConstructionError
        except InvalidValuesError:
            raise TableConstructionError
        except TableConstructionError:
            raise 

    def candles_setup(self):
        # Candle ID:
        #   [symbol]-[start]
        candles_def = {
            "candle_id": "TEXT PRIMARY KEY UNIQUE",
            "date": "DATE",
            "start": "INT",
            "trading_pair": "TEXT",
            "open": "REAL",
            "high": "REAL",
            "low": "REAL",
            "close": "REAL",
            "volume": "REAL",
        }
        try:
            self.create_table(table_name='candles', table_definition=self.table_definitions['candles'])
        except InvalidTableNameError:
            raise TableConstructionError
        except InvalidValuesError:
            raise TableConstructionError
        except TableConstructionError:
            raise 

    def market_trades_setup(self):
        # Trade ID:
        #   DEFINED BY COINBASE API
        market_trades_def = {
            "trade_id": "TEXT PRIMARY KEY UNIQUE",
            "trading_pair": "TEXT",
            "price": "REAL",
            "size": "REAL",
            "time": "DATETIME",
            "side": "TEXT",
            "bid": "REAL",
            "ask": "REAL",
            "exchange": "TEXT"
        }
        # Candle ID:
        #   [symbol]-[start]
        market_candles_def = {
            "candle_id": "TEXT PRIMARY KEY UNIQUE",
            "time": "DATETIME",
            "start": "INT",
            "trading_pair": "TEXT",
            "open": "REAL",
            "high": "REAL",
            "low": "REAL",
            "close": "REAL",
            "volume": "REAL",
        }
        try:
            self.create_table(table_name="market_trade", table_definition=self.table_definitions['market_trade'])
            self.create_table(table_name="market_candles", table_definition=self.table_definitions['market_candles'])
        except InvalidTableNameError:
            raise TableConstructionError
        except InvalidValuesError:
            raise TableConstructionError
        except TableConstructionError:
            raise 
