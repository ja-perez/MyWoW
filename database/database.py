import sqlite3
import datetime
from os import path, getcwd, listdir
import json

data_dir = path.join(getcwd(), 'data')

class InvalidTableNameError(Exception):
    pass

class InvalidValuesError(Exception):
    pass

class InvalidInsertError(Exception):
    pass

class Database:
    def __init__(self, db_name: str = ''):
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
    def insert_one(self, values: list | dict, table_name: str = None):
        if not values:
            raise InvalidInsertError
        if type(values) == dict:
            table_schema = self.get_row_schema(table_name)
            for key in table_schema:
                table_schema[key] = values[key]
            values = [table_schema[key] for key in table_schema]

        formatted_values = []
        for val in values:
            formatted_values.append(self.format_value(val))

        p_index, p_col = self.get_table_primary_key(table_name=table_name)
        duplicate = self.get_rows(table_name=table_name, where_statement=f"WHERE {p_col}={formatted_values[p_index]}")
        if duplicate:
            print(f'Failed INSERT: Duplicate "{p_col}" found.')
            return

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

    @staticmethod
    def build_where(eq: dict={}, lt: dict={}, gt: dict={}, lte: dict={}, gte: dict={}, btwn: dict={}) -> str:
        """Constructs a where statement that requires all conditions be met.

        :eq, lt, gt, lte, gte: { column_name : value, ... }

        :btwn: { column_name : { 'min': value, 'max': value }, ... }

        Notes: 
            - Between (btwn) comparison is inclusive for min and max values. 
            - If the condition contains a string, it must be passed with alternating apostraphes and quotation marks, ex: "'John'" or '"John"'

        Example: 
        - build_where_with_conditions(eq={'name':"'John'"}, gt={'account_total':500}, lte={'items_purchased':10})
        #prints "WHERE name='John' AND account_total>500 AND items_purchased<=10"

        Return: 
            - String: "WHERE name='John' AND account_total>500 AND items_purchased<=10"
        """
        where_conditions = []
        if eq:
            where_conditions.extend([f"{col_name}={eq[col_name]}" for col_name in eq])
        if btwn:
            where_conditions.extend([f"{col_name}>={btwn[col_name]['min']}" for col_name in btwn])
            where_conditions.extend([f"{col_name}<={btwn[col_name]['max']}" for col_name in btwn])
        if lt:
            where_conditions.extend([f"{col_name}<{eq[col_name]}" for col_name in lt])
        if lte:
            where_conditions.extend([f"{col_name}<={eq[col_name]}" for col_name in lte])
        if gt:
            where_conditions.extend([f"{col_name}>{eq[col_name]}" for col_name in gt])
        if gte:
            where_conditions.extend([f"{col_name}>={eq[col_name]}" for col_name in gte])
        return f"WHERE {' AND '.join(where_conditions)}"

    @check_table
    def get_rows(self, table_name: str = None, limit: int = 20, where_statement: str = '', headers: list[str] = None) -> list[dict[str: str | float | int | datetime.datetime]]:
        if headers:
            header_query = ', '.join(headers)
        else:
            header_query = '*'

        limit_statement = f"{f'LIMIT {limit}' if limit != -1 else ''}"

        query = f"SELECT {header_query} FROM {table_name}" + f" {where_statement} " + f" {limit_statement}"
        res = self.cur.execute(query)
        rows = res.fetchall()
        return [self.format_row(row=row, table_name=table_name, headers=headers) for row in rows]

    @check_table
    def get_row_schema(self, table_name: str = None) -> dict[str: None]:
        table_schema = self.get_table_schema(table_name=table_name)
        return {
            key: None for key in table_schema
        }

    @check_table
    def get_table_schema(self, table_name: str = None) -> dict[str:str]:
        """
        return_value: { col_name : col_type, ... }
        """
        query = f"PRAGMA table_info({table_name})"
        self.cur.execute(query)
        res = self.cur.fetchall()
        schema = {
            col[1] : col[2] for col in res
        }
        return schema

    @check_table
    def get_table_primary_key(self, table_name: str = None) -> list[int, str]:
        query = self.cur.execute(f"PRAGMA table_info({table_name})")
        table_info = query.fetchall()
        for col_info in table_info:
            if col_info[-1] == 1:
                return col_info[:2]

    @check_table
    def format_row(self, row: list[str], table_name: str = None, headers: list[str] = None) -> dict[str: str | float | int | datetime.datetime]:
        """
        return_value: [ col_value, ... ]
        """
        schema = self.get_table_schema(table_name)
        if headers:
            schema = { header: schema[header] for header in schema if header in headers}
        else:
            headers = [ header for header in schema ]

        formatted_row = {}
        for i, col_name in enumerate(headers):
            col_type = schema[col_name]
            if col_type == "TEXT":
                formatted_row[col_name] = row[i]
            if col_type == "REAL" or col_type == "FLOAT":
                formatted_row[col_name] = float(row[i])
            if col_type == "INT":
                formatted_row[col_name] = int(row[i])
            if col_type == "DATE":
                formatted_row[col_name] = row[i]

        return formatted_row

def get_predictions_data():
    predictions_data_path = path.join(data_dir, "dummy_data.csv")
    predictions_data = []
    with open(predictions_data_path, 'r') as f:
        for line in f:
            predictions_data.append(line.strip().split(','))

    data = []
    for row in predictions_data:
        symbol: str = row[0]
        trading_pair = row[1]
        start_date = datetime.datetime.strptime(row[2], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(row[3], "%Y-%m-%d")
        start_price = float(row[4])
        end_price = float(row[5])
        buy_price = float(row[6])
        sell_price = float(row[7])

        prediction_id = f"{symbol.upper()}-{start_date.month}{start_date.day}{end_date.month}{end_date.day}-{start_date.year}"

        data.append([
            prediction_id,
            symbol,
            trading_pair,
            datetime.datetime.strftime(start_date, "%Y-%m-%d"),
            datetime.datetime.strftime(end_date, "%Y-%m-%d"),
            start_price,
            end_price,
            buy_price,
            sell_price,
        ])
    return data

def predictions_setup(db: Database):
    try:
        # Setting up predictions table
        predictions_def = {
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
        }
        db.create_table(table_name="predictions", values=predictions_def)
        db.set_table(table_name="predictions")

        # Seeding db with data currently in csv file "dummy_predictions"
        predictions_data = get_predictions_data()
        for data in predictions_data:
            db.insert_one(data)

    except InvalidTableNameError:
        raise
    except InvalidInsertError:
        raise
    except InvalidValuesError:
        raise

def get_results_data():
    results_data_path = path.join(data_dir, "dummy_results.csv")
    results_data = []
    with open(results_data_path, 'r') as f:
        for line in f:
            results_data.append(line.strip().split(','))

    data = []
    for row in results_data:
        symbol: str = row[0]
        trading_pair = row[1]
        start_date = datetime.datetime.strptime(row[2], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(row[3], "%Y-%m-%d")
        start_price = float(row[4])
        end_price = float(row[5])
        buy_price = float(row[6])
        sell_price = float(row[7])
        close_price = float(row[8])

        prediction_id = f"{symbol.upper()}-{start_date.month}{start_date.day}{end_date.month}{end_date.day}-{start_date.year}"

        data.append([
            prediction_id,
            symbol,
            trading_pair,
            datetime.datetime.strftime(start_date, "%Y-%m-%d"),
            datetime.datetime.strftime(end_date, "%Y-%m-%d"),
            start_price,
            end_price,
            buy_price,
            sell_price,
            close_price
        ])
    return data

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
            "close_price": "REAL",
        }
        db.create_table(table_name="results", values=results_def)
        db.set_table(table_name="results")

        data_copy = db.get_rows(table_name='temp_results', limit=-1)
        for data in data_copy:
            db.insert_one(values=data)
        
        # Seeding db with data currently in csv file "dummy_results"
        # results_data = get_results_data()
        # for data in results_data:
        #     db.insert_one(data)

    except InvalidTableNameError:
        raise
    except InvalidInsertError:
        raise
    except InvalidValuesError:
        raise

def get_candle_data():
    candle_files = [path.join(data_dir, file) for file in listdir(data_dir) if file.endswith("candles.json")]
    for file_path in candle_files:
        file_name: str = path.basename(file_path)
        file_name_parts = file_name.split('_')
        trading_pair = file_name_parts[2].upper()

        with open(file_path, 'r') as f:
            file_data = json.load(f)
        data = []
        for row in file_data:
            start = int(row['start'])
            date = datetime.datetime.fromtimestamp(start).strftime("%Y-%m-%d")
            candle_open = float(row['open'])
            high = float(row['high'])
            low = float(row['low'])
            close = float(row['close'])
            volume = float(row['volume'])
            data.append([
                date,
                start,
                trading_pair,
                candle_open,
                high,
                low,
                close,
                volume,
            ])
        return data

def candles_setup(db: Database):
    try:
        # Setting up candles table
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
        db.create_table("candles", candles_def)

        # Seeding db with *candles.json files in data dir
        # candle_data = get_candle_data()
        # for data in candle_data:
        #     db.insert_one(data)

    except InvalidTableNameError as e:
        raise
    except InvalidInsertError as e:
        raise
    except InvalidValuesError as e:
        raise

def MyWoWSetup():
    db = Database(db_name="mywow.db")

    try:
        # predictions_setup(db)
        # results_setup(db)
        # candles_setup(db)
        pass
    except InvalidTableNameError as e:
        print(f"Invalid Table Name")
    except InvalidInsertError as e:
        print(f"Invalid Insert")
    except InvalidValuesError as e:
        print(f"Invalid Values")
    except Exception as e:
        print(f"UNKNOWN ERROR: {e}")
    finally:
        db.on_exit()

def main():
    MyWoWSetup()

if __name__=="__main__":
    main()