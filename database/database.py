import sqlite3
import utils.utils

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
    def get_rows(self, table_name: str = None, limit: int = 20, where_values: dict = {}):
        if where_values:
            where_query = f"WHERE {" AND ".join(self.format_dict_values(where_values))}"
        else:
            where_query = ""

        query = f"SELECT * FROM {table_name}" + f" {where_query} " + f" LIMIT {limit}"
        res = self.cur.execute(query)
        rows = res.fetchall()
        return rows

    def get_table_schema(self, table_name: str = None):
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

def MyWoWSetup():
    db = Database(db_name="mywow.db")

    try:
        # Setting up predictions table
        results_def = {
            # [symbol]-[start_month][start_day][end_month][end_day]-[symbol count]-[P]
            # SHIB-12151218-005-P, SHIB-12151218-006-P
            "prediction_id": "TEXT",
            # [symbol]-[start_month][start_day][end_month][end_day]-[symbol count]-[R]
            # SHIB-12151218-005-R, SHIB-12151218-006-R
            "result_id": "TEXT PRIMARY KEY",
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
            insert_data = [
                row[0],
                row[1],
                row[2],
                row[3],
                float(row[4]),
                float(row[5]),
                float(row[6]),
                float(row[7]),
                float(row[8]),
            ]
            db.insert_one(insert_data)

        shib_results = db.get_rows(where_values={"symbol":"SHIB"})        
        print("SHIB Results:")
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

if __name__=='__main__':
    main()