from sqlalchemy import create_engine
import urllib

driver = urllib.parse.quote_plus("ODBC Driver 17 for SQL Server")
DATABASE_URL = f"mssql+pyodbc://sa:Strong_Password123!@localhost:1433/NoxyChatbotDB?driver={driver}"

try:
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    print("Connected!")
    conn.close()
except Exception as e:
    print("Connection failed!")
    print(e)
