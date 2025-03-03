import sqlite3
import datetime
import json
from typing import Any, Optional
from os import path, getcwd

data_dir = path.join(getcwd(), 'data')

class InvalidTableNameError(Exception):
    pass

class InvalidValuesError(Exception):
    pass

class InvalidInsertError(Exception):
    pass

class DuplicateInsertError(Exception):
    pass

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        db_path = path.join(data_dir, db_name)
        self.conn = sqlite3.connect(db_path)

        self.cur = self.conn.cursor()
        self.table_name = ''
    
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

    def check_table(func: Any):
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

        definitions = [
            " ".join([key, values[key]]) for key in values
        ]
        definition = ", ".join(definitions)
        query = f"CREATE TABLE {table_name}({definition})"
        self.cur.execute(query)

    def set_table(self, table_name: str):
        if self.table_exists(table_name):
            self.table_name = table_name
        else:
            raise InvalidTableNameError

    @staticmethod
    def format_value(value) -> str:
        if value == '':
            return f"''"

        if type(value) == str:
            return f"'{value}'"
        elif type(value) == datetime.datetime:
            return f"'{value.isoformat()}'"
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
    def insert_one(self, values: list | dict, table_name: Optional[str] = None):
        if not values:
            raise InvalidValuesError
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
            # raise DuplicateInsertError
            return

        query = f"INSERT INTO {table_name} VALUES ({', '.join(formatted_values)})"
        self.cur.execute(query)
        self.conn.commit()

    @check_table
    def update_where(self, updated_values: dict, where_values: dict, table_name: Optional[str] = None):
        if not updated_values or not where_values:
            raise InvalidValuesError

        formatted_update_values = self.format_dict_values(updated_values)
        formatted_where_values = self.format_dict_values(where_values)
        
        query = f"UPDATE {table_name} SET {",".join(formatted_update_values)} WHERE {" AND ".join(formatted_where_values)}"
        self.cur.execute(query)
        self.conn.commit()

    @check_table
    def delete_where(self, values: dict, table_name: Optional[str] = None):
        if not values:
            raise InvalidValuesError

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
    def get_rows(self, table_name: Optional[str] = None, limit: int = -1, where_statement: str = '', order_by_statement: str = '', headers: Optional[list[str]] = None) -> list[ dict[ str, str | float | int | datetime.datetime ] ]:
        if headers:
            header_query = ', '.join(headers)
        else:
            header_query = '*'

        limit_statement = f"{f'LIMIT {limit}' if limit != -1 else ''}"

        query = f"SELECT {header_query} FROM {table_name}" + f" {where_statement} " + f" {order_by_statement}" f" {limit_statement}"
        res = self.cur.execute(query)
        rows = res.fetchall()
        return [self.format_row(row=row, table_name=table_name, headers=headers) for row in rows]

    @check_table
    def get_row_schema(self, table_name: Optional[str] = None) -> dict[str, None]:
        table_schema = self.get_table_schema(table_name=table_name)
        return {
            key: None for key in table_schema
        }

    @check_table
    def get_table_schema(self, table_name: Optional[str] = None) -> dict[str, str]:
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
    def column_is_unique(self, column_name: str, table_name: Optional[str] = None):
        query = f"PRAGMA index_list({table_name})"
        self.cur.execute(query)
        res = self.cur.fetchall()
        
        for unique_col in res:
            index_name = unique_col[1]
            query = f"PRAGMA index_info({index_name})"
            self.cur.execute(query)
            col_info = self.cur.fetchall()[0]
            if col_info[-1] == column_name:
                return True

        return False

    @check_table
    def get_table_def(self, table_name: Optional[str] = None) -> dict[str, str]:
        query = f"PRAGMA table_info({table_name})"
        self.cur.execute(query)
        res = self.cur.fetchall()

        pk_index, pk_name = self.get_table_primary_key(table_name=table_name)
        table_def: dict[str, str] = {}
        for col in res:
            col_name: str = str(col[1])
            col_type: str = str(col[2]).upper()

            col_def = col_type
            if col_name == pk_name:
                col_def += " PRIMARY KEY"
            if self.column_is_unique(column_name=col_name, table_name=table_name):
                col_def += " UNIQUE"

            table_def[col_name] = col_def
        
        return table_def

    @check_table
    def get_table_primary_key(self, table_name: Optional[str] = None) -> list[int | str]:
        query = self.cur.execute(f"PRAGMA table_info({table_name})")
        table_info = query.fetchall()
        for col_info in table_info:
            if col_info[-1] == 1:
                return col_info[:2]
        return [-1, '']

    @check_table
    def format_row(self, row: list[str], table_name: Optional[str] = None, headers: Optional[list[str]] = None) -> dict[ str, str | float | int | datetime.datetime]:
        """
        return_value: [ col_value, ... ]
        """
        schema = self.get_table_schema(table_name)
        if headers:
            schema = { header: schema[header] for header in schema if header in headers}
        else:
            headers = [ header for header in schema ]

        formatted_row: dict[str, str | float | int | datetime.datetime] = {}
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
            if col_type == "DATETIME":
                formatted_row[col_name] = datetime.datetime.fromisoformat(row[i])

        return formatted_row

def main():
    pass

if __name__=="__main__":
    main()