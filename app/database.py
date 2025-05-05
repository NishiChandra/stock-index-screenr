import duckdb
from utils import DB_PATH, logger
import pandas as pd
def get_db_connection():
    """Returns a connection to the DuckDB database."""
    try:
        return duckdb.connect(DB_PATH)
    except Exception as e:
        logger.error(f"Error connecting to DuckDB: {e}")
        raise
def reset_database():
    """Drops existing tables in proper order to handle dependencies"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("Dropping existing tables...")

        # Drop tables in reverse dependency order
        cursor.execute("DROP TABLE IF EXISTS index_performance")
        cursor.execute("DROP TABLE IF EXISTS index_composition")
        cursor.execute("DROP TABLE IF EXISTS daily_data")
        cursor.execute("DROP TABLE IF EXISTS stock_metadata")
        
        conn.commit()
        logger.info("Database reset complete.")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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
def fetch_stock_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create tables with DuckDB-compatible syntax
        cursor.execute("""SELECT * from index_performance""")
        metadata = cursor.fetchall()
        # metadata_df = pd.DataFrame(metadata, columns=['symbol', 'name'])
        print(metadata)
        cursor.execute("""SELECT * from index_composition""")
        daily_data = cursor.fetchall()
        # daily_df = pd.DataFrame(daily_data, columns=['symbol', 'date', 'market_cap', 'price'])
        # print(daily_df)
        conn.commit()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # reset_database()
    # setup_database()
    fetch_stock_data()