import duckdb
from app.utils import DB_PATH, logger
import pandas as pd
def get_db_connection():
    """Returns a connection to the DuckDB database."""
    try:
        return duckdb.connect(DB_PATH)
    except Exception as e:
        logger.error(f"Error connecting to DuckDB: {e}")
        raise

def setup_database():
    """Sets up the database schema without auto-incrementing IDs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create tables with symbol as primary key
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_metadata (
                symbol VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_data (
                symbol VARCHAR NOT NULL,
                date DATE NOT NULL,
                market_cap DOUBLE NOT NULL,
                price DOUBLE NOT NULL,
                FOREIGN KEY (symbol) REFERENCES stock_metadata(symbol),
                UNIQUE (symbol, date)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS index_composition (
                date DATE NOT NULL,
                symbol VARCHAR NOT NULL,
                weight DOUBLE NOT NULL,
                FOREIGN KEY (symbol) REFERENCES stock_metadata(symbol),
                UNIQUE (date, symbol)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS index_performance (
                date DATE PRIMARY KEY,
                index_value DOUBLE NOT NULL,
                daily_return DOUBLE,
                cumulative_return DOUBLE
            )
        """)

        conn.commit()
        logger.info("Database setup complete.")
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_database()
