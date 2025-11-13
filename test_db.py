from sqlalchemy import create_engine
import urllib
import os
from dotenv import load_dotenv

load_dotenv()

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DB = os.getenv("SQL_DB")
SQL_USER = os.getenv("SQL_USER")
SQL_PASS = os.getenv("SQL_PASS")

driver = urllib.parse.quote_plus("ODBC Driver 17 for SQL Server")
DATABASE_URL = f"mssql+pyodbc://{SQL_USER}:{SQL_PASS}@{SQL_SERVER}/{SQL_DB}?driver={driver}"

try:
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    print("Connected!")
    conn.close()
except Exception as e:
    print("Connection failed!")
    print(e)
