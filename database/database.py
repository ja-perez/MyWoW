import sqlite3
import utils.utils
import datetime
from os import path

class InvalidTableNameError(Exception):
    pass

class InvalidValuesError(Exception):
    pass

class InvalidInsertError(Exception):
    pass

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)

        self.cur = self.conn.cursor()
        self.table_name = None
    
    def on_exit(self):
        print(f"Closing connection to database {self.db_name}...")
        self.cur.close()
        self.conn.close()

    def table_exists(self, table_name: str):
        if not table_name or table_name.strip() == "":
            return False
        
        res = self.cur.execute(f"PRAGMA table_info({table_name})")
        table_info = res.fetchall()
        if table_info:
            return True
        else:
            return False

    def check_table(func):
        def wrapper(self, *args, **kwargs):
            if args:
                for arg in args:
                    if type(arg) != str:
                        continue
                    if self.table_exists(arg):
                        return func(self, *args, **kwargs)

            table_name = kwargs.get('table_name', self.table_name)
            if not table_name or table_name.strip() == "" or not self.table_exists(table_name):
                raise InvalidTableNameError
            else:
                kwargs['table_name'] = table_name
            return func(self, *args, **kwargs)
        return wrapper

    def create_table(self, table_name: str, values: dict):
        if not table_name:
            raise InvalidTableNameError
        elif self.table_exists(table_name):
            return

        if not values:
            raise InvalidValuesError

        def is_any(type_value: str | None):
            if not type_value or type_value.strip() == "":
                return True
            if type_value == "ANYTHING" or type_value == "NONE":
                return True
            return False
        for key in values:
            val: str = values[key]
            if is_any(val):
                values[key] = "ANYTHING"
            else:
                values[key] = val.upper()

        definition = [
            " ".join([key, values[key]]) for key in values
        ]
        definition = ", ".join(definition)
        query = f"CREATE TABLE {table_name}({definition})"
        self.cur.execute(query)

    def set_table(self, table_name: str):
        if self.table_exists(table_name):
            self.table_name = table_name
        else:
            raise InvalidTableNameError

    @staticmethod
    def format_value(value) -> str:
        if not value:
            return ""
    
        if type(value) == str:
            return f"'{value}'"
        else:
            return str(value)

    def format_dict_values(self, values: dict) -> list[str]:
        if not values:
            return []

        updated_values = []
        for col_name in values:
            val = values[col_name]
            updated_values.append(f"{col_name}={self.format_value(val)}")

        return updated_values

    @check_table
    def insert_one(self, values: list, table_name: str = None):
        if not values:
            raise InvalidInsertError

        formatted_values = []
        for val in values:
            formatted_values.append(self.format_value(val))

        query = f"INSERT INTO {table_name} VALUES ({', '.join(formatted_values)})"
        self.cur.execute(query)
        self.conn.commit()

    @check_table
    def update_where(self, updated_values: dict, where_values: dict, table_name: str = None):
        if not updated_values or not where_values:
            raise InvalidValuesError

        formatted_update_values = self.format_dict_values(updated_values)
        formatted_where_values = self.format_dict_values(where_values)
        
        query = f"UPDATE {table_name} SET {",".join(formatted_update_values)} WHERE {" AND ".join(formatted_where_values)}"
        self.cur.execute(query)
        self.conn.commit()

    @check_table
    def delete_where(self, values: dict, table_name: str = None):
        if not values:
            raise InvalidInsertError

        formatted_values = self.format_dict_values(values)
        
        query = f"DELETE FROM {table_name} WHERE {" AND ".join(formatted_values)}"
        self.cur.execute(query)
        self.conn.commit()

    @check_table
    def get_rows(self, table_name: str = None, limit: int = 20, where_values: dict = {}, headers: list[str] = None) -> list[list[str | float | int | datetime.datetime]]:
        if where_values:
            where_query = f"WHERE {" AND ".join(self.format_dict_values(where_values))}"
        else:
            where_query = ""

        if headers:
            header_query = ', '.join(headers)
        else:
            header_query = '*'

        query = f"SELECT {header_query} FROM {table_name}" + f" {where_query} " + f" LIMIT {limit}"
        res = self.cur.execute(query)
        rows = res.fetchall()
        return [self.format_row(row=row, table_name=table_name, headers=headers) for row in rows]

    def get_table_schema(self, table_name: str = None) -> dict[str:str]:
        """
        return_value: { col_name : col_type, ... }
        """
        table_name = table_name if table_name else self.table_name
        if not table_name or not self.table_exists(table_name):
            raise InvalidTableNameError

        query = f"PRAGMA table_info({table_name})"
        self.cur.execute(query)
        res = self.cur.fetchall()
        schema = {
            col[1] : col[2] for col in res
        }
        return schema

    @check_table
    def format_row(self, row: list[str], table_name: str = None, headers: list[str] = None) -> list[str | float | int | datetime.datetime]:
        """
        return_value: [ col_value, ... ]
        """
        schema = self.get_table_schema(table_name)
        if headers:
            schema = { header: schema[header] for header in schema if header in headers}

        formatted_row = []
        for i, col_name in enumerate(headers):
            col_type = schema[col_name]
            if col_type == "TEXT":
                formatted_row.append(row[i])
            if col_type == "REAL":
                formatted_row.append(float(row[i]))
            if col_type == "INT":
                formatted_row.append(int(row[i]))
            if col_type == "DATE":
                formatted_row.append(datetime.datetime.strptime(row[i], "%Y-%m-%d"))

        return formatted_row

def results_setup(db: Database):
    try:
        # Setting up results table
        results_def = {
            # [symbol]-[start_month][start_day][end_month][end_day]-[start_year]
            # SHIB-12151218-2024, GTC-12151218-2024
            "prediction_id": "TEXT PRIMARY KEY UNIQUE",
            "symbol": "TEXT",
            "trading_pair": "TEXT",
            "start_date": "DATE",
            "end_date": "DATE",
            "start_price": "REAL",
            "end_price": "REAL",
            "buy_price": "REAL",
            "sell_price": "REAL",
            "actual_end_price": "REAL",
        }
        db.create_table("results", results_def)
        db.set_table("results")

        # Seeding db with data currently in csv file "dummy_results"
        results_data = utils.get_csv_data_from_file(utils.get_path_from_data_dir("dummy_results.csv"))
        for row in results_data:
            symbol: str = row[0]
            trading_pair = row[1]
            start_date = datetime.datetime.strptime(row[2], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(row[3], "%Y-%m-%d")
            start_price = float(row[4])
            end_price = float(row[5])
            buy_price = float(row[6])
            sell_price = float(row[7])
            actual_end_price = float(row[8])

            prediction_id = f"{symbol.upper()}-{start_date.month}{start_date.day}{end_date.month}{end_date.day}-{start_date.year}"

            insert_data = [
                prediction_id,
                symbol,
                trading_pair,
                datetime.datetime.strftime(start_date, "%Y-%m-%d"),
                datetime.datetime.strftime(end_date, "%Y-%m-%d"),
                start_price,
                end_price,
                buy_price,
                sell_price,
                actual_end_price
            ]
            db.insert_one(insert_data)

    except InvalidTableNameError:
        raise
    except InvalidInsertError:
        raise
    except InvalidValuesError:
        raise

def candles_setup(db: Database):
    try:
        # Setting up candles table
        candles_def = {
            "date": "DATE",
            "start": "INT",
            "trading_pair": "TEXT",
            "open": "FLOAT",
            "high": "FLOAT",
            "low": "FLOAT",
            "close": "FLOAT",
            "volume": "FLOAT",
        }
        db.create_table("candles", candles_def)
        db.set_table("candles")

        # Seeding db with *candles.json files in data dir
        candle_files = utils.get_files_by_extension(utils.get_path_from_data_dir(), "candles.json")
        for file_path in candle_files:
            file_name: str = path.basename(file_path)
            file_name_parts = file_name.split('_')
            trading_pair = file_name_parts[2].upper()

            file_data = utils.get_dict_data_from_file(file_path)
            for row in file_data:
                start = int(row['start'])
                date = utils.unix_to_date_string(start)
                open = float(row['open'])
                high = float(row['high'])
                low = float(row['low'])
                close = float(row['close'])
                volume = float(row['volume'])

                insert_data = [
                    date,
                    start,
                    trading_pair,
                    open,
                    high,
                    low,
                    close,
                    volume,
                ]
                db.insert_one(insert_data)

    except InvalidTableNameError as e:
        raise
    except InvalidInsertError as e:
        raise
    except InvalidValuesError as e:
        raise

def MyWoWSetup():
    db = Database(db_name="mywow.db")

    try:
        # results_setup()
        # candles_setup()
        shib_results = db.get_rows("results", where_values={'symbol':'SHIB'}, headers=['symbol', 'start_price', 'start_date'])
        for result in shib_results:
            print(result)
    except InvalidTableNameError as e:
        print(f"Invalid Table Name")
    except InvalidInsertError as e:
        print(f"Invalid Insert")
    except InvalidValuesError as e:
        print(f"Invalid Values")
    finally:
        db.on_exit()

def main():
    pass

if __name__=="__main__":
    main()