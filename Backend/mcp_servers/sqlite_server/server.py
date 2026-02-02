from mcp.server.fastmcp import FastMCP
import sqlite3
import pandas as pd
import os

# Initialize FastMCP Server
mcp = FastMCP("sqlite-server")

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/ecommerce.db"))

def get_connection():
    return sqlite3.connect(DB_PATH)

@mcp.tool()
def list_tables() -> str:
    """List all tables in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return f"Tables in database: {', '.join(tables)}"

@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get the schema/columns of a specific table."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(f"PRAGMA table_info({table_name})", conn)
        conn.close()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error describing table: {str(e)}"

@mcp.tool()
def query_database(sql_query: str) -> str:
    """Execute a READ-ONLY SQL query. Only SELECT statements are allowed."""
    if not sql_query.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed for security."
    
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error executing SQL: {str(e)}"

if __name__ == "__main__":
    mcp.run()
