from alembic import context
from sqlalchemy import engine_from_config, pool
import urllib
from alembic import context

config = context.config

driver = urllib.parse.quote_plus("ODBC Driver 17 for SQL Server")
config.set_main_option(
    "sqlalchemy.url",
    f"mssql+pyodbc://sa:Strong_Password123!@localhost:1433/NoxyChatbotDB?driver={driver}"
)