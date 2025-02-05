import os

from database.database import Database, InvalidTableNameError, InvalidValuesError, DuplicateInsertError

class DBMSConstructionError(Exception):
    """Raised when a database management system object cannot be created"""
    pass

class TableConstructionError(Exception):
    """Raised when a table cannot be created in a database"""
    pass

class InvalidLocalStorageError(Exception):
    """Raised when data found in local storage is invalid due to formatting or configuration"""
    pass

class InvalidDataSourceError(Exception):
    """Raised when data is requested from an invalid table name or file path """
    pass

class MyWoWDatabase:
    data_dir = os.path.join(os.getcwd(), 'data')
    local_db_path = os.path.join(data_dir, 'local_db')
    candles_dir = os.path.join(data_dir, 'candles')

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
        self.setup_database()

    def setup_database(self):
        self.setup_local_storage()
        for name, definition in self.table_definitions.items():
            try:
                self.create_table(table_name=name, table_definition=definition)
                self.upload_local_table_data(table_name=name)
            except TableConstructionError:
                raise DBMSConstructionError

    def setup_local_storage(self):
        # directories
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        if not os.path.exists(self.local_db_path):
            os.mkdir(self.local_db_path) 
        if not os.path.exists(self.candles_dir):
            os.mkdir(self.candles_dir)

    def create_table(self, table_name: str, table_definition: dict[str, str]):
        try:
            # database
            if self.db.table_exists(table_name):
                existing_table_def = self.db.get_table_def(table_name)
                if existing_table_def != table_definition:
                    raise TableConstructionError
            else:
                self.db.create_table(table_name=table_name, values=table_definition)

            # local
            local_table_path = os.path.join(self.local_db_path, table_name + '.csv')
            if os.path.exists(local_table_path):
                with open(local_table_path, 'r') as f:
                    local_header = f.readline().strip('\n')
                    if local_header != ','.join(table_definition.keys()):
                        # Need to raise error as we have to assume all data in file follows the format of the incorrect header
                        raise InvalidLocalStorageError
            else:
                with open(local_table_path, 'x') as f:
                    f.write(','.join(table_definition.keys()) + '\n')
        except InvalidTableNameError:
            raise TableConstructionError
        except InvalidValuesError:
            raise TableConstructionError
        except TableConstructionError:
            raise

    def upload_local_table_data(self, table_name: str):
        local_table_path = os.path.join(self.local_db_path, table_name + '.csv')
        with open(local_table_path, 'r') as f:
            _header = f.readline()
            rows = [line.strip('\n').split(',') for line in f.readlines()]
            data = []
            for row in rows:
                header = [col_name for col_name in self.table_definitions[table_name]]
                header_to_value = {
                    header[i]: value for i, value in enumerate(row)
                }
                data.append(header_to_value)

            for values in data:
                try:
                    self.add_item(table_name=table_name, values=values)
                except DuplicateInsertError:
                    continue
                except InvalidValuesError:
                    continue

    def get_items(self, table_name: str, start_index: int = 0, limit: int = 10, where_statement: str = "") -> list:
        if table_name not in self.table_definitions:
            raise InvalidDataSourceError

        # TODO: Handle using local data as backup to missing database connection

        res = self.db.get_rows(table_name=table_name, limit=limit, where_statement=where_statement)
        return res[start_index:]

    def add_item(self, table_name: str, values: list | dict):
        if table_name not in self.table_definitions:
            raise InvalidDataSourceError
        
        # TODO: Handle using local data as backup to missing database connection

        res = self.db.insert_one(table_name=table_name, values=values)

    def remove_item(self, table_name: str, values: dict):
        if table_name not in self.table_definitions:
            raise InvalidDataSourceError

        # TODO: Handle using local data as backup to missing database connection

        self.db.delete_where(table_name=table_name, values=values)