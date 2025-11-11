import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import urllib

load_dotenv()

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DB = os.getenv("SQL_DB")
SQL_USER = os.getenv("SQL_USER")
SQL_PASS = os.getenv("SQL_PASS")

driver = urllib.parse.quote_plus("ODBC Driver 17 for SQL Server")
DATABASE_URL = f"mssql+pyodbc://sa:Strong_Password123!@localhost:1433/NoxyChatbotDB?driver={driver}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


