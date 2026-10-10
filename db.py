# db.py
import os
import struct
import pyodbc
from azure.identity import AzureCliCredential

def get_connection():
    """Acquires an Azure CLI Entra token and returns a pyodbc connection to Azure SQL."""
    credential = AzureCliCredential()
    token = credential.get_token("https://database.windows.net/.default")
    
    # Construct connection string using token bytes
    token_bytes = token.token.encode("utf-16-le")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    attrs_connection = {1256: token_struct}  # SQL_COPT_SS_ACCESS_TOKEN
    
    server = os.getenv("AZURE_SQL_SERVER", "your-server.database.windows.net")
    database = os.getenv("AZURE_SQL_DATABASE", "marketdata")
    driver = "{ODBC Driver 18 for SQL Server}"
    
    conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};"
    return pyodbc.connect(conn_str, attrs_before=attrs_connection)