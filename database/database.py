import pymssql
import dotenv

class Database:
    pass


def main():
    conn = pymssql.connect(
        server=r"localhost",
        user=r"admin",
        password=r"letmein",
        database=r"adventureworks",
        as_dict=True,
        tds_version="7.0"
    )

    cursor = conn.cursor()

    query = """
SELECT TOP 5 CustomerID,
FROM SalesLT.Customer
"""
    cursor.execute(query)
    records = cursor.fetchall()

    for r in records:
        print(f"{r['CustomerID']}")



if __name__=='__main__':
    main()