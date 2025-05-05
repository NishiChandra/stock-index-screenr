import requests
from requests.exceptions import RequestException
import yfinance as yf
from utils import logger
import datetime
from database import duckdb,get_db_connection
import pandas as pd
import lxml

def get_sp500_tickers():
    """Scrape S&P 500 constituents from Wikipedia"""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    sp500_table = tables[0]
    return sp500_table['Symbol'].tolist()

def get_nasdaq100_tickers():
    """Scrape NASDAQ-100 constituents from Wikipedia"""
    url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    tables = pd.read_html(url)
    nasdaq_table = tables[4]  # Might need to adjust this index if Wikipedia changes
    return nasdaq_table['Ticker'].tolist()

def get_stock_universe():
    """Combine both indices and remove duplicates"""
    # sp500 = get_sp500_tickers()
    nasdaq100 = get_nasdaq100_tickers()

    # return list(set(sp500 + nasdaq100))
    return list(set(nasdaq100))

def fetch_stock_data(tickers, days=40):
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=days * 2)
    all_data = []

    for symbol in tickers:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            shares = ticker.info.get("sharesOutstanding")

            if hist.empty or not shares:
                continue

            hist = hist.reset_index()
            hist["symbol"] = symbol
            hist["price"] = hist["Close"]
            hist["market_cap"] = hist["price"] * shares
            all_data.append(hist[["Date", "symbol", "price", "market_cap"]])
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            continue

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def store_stock_data(df: pd.DataFrame):
    """Store stock data using symbols as primary keys with batch operations"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Convert dates to proper format
        df['Date'] = pd.to_datetime(df['Date']).dt.date

        # 1. Handle stock metadata first
        # Get unique symbols from the dataframe
        symbols = df['symbol'].unique().tolist()
        
        # Find existing symbols in database
        cursor.execute(f"""
            SELECT symbol FROM stock_metadata 
            WHERE symbol IN ({','.join(['?']*len(symbols))})
        """, symbols)
        existing_symbols = {row[0] for row in cursor.fetchall()}
        
        # Identify new symbols to insert
        new_symbols = [sym for sym in symbols if sym not in existing_symbols]
        
        if new_symbols:
            # Batch fetch company names
            symbols_with_names = []
            for symbol in new_symbols:
                try:
                    name = yf.Ticker(symbol).info.get('longName', symbol)
                except Exception:
                    name = symbol
                symbols_with_names.append((symbol, name))
            
            # Batch insert new symbols
            cursor.executemany(
                "INSERT INTO stock_metadata (symbol, name) VALUES (?, ?)",
                symbols_with_names
            )

        # 2. Handle daily data with batch insert
        # Prepare records
        daily_records = [
            (row['symbol'], row['Date'], row['market_cap'], row['price'])
            for _, row in df.iterrows()
        ]
        
        # Batch insert with conflict ignore
        cursor.executemany("""
            INSERT OR IGNORE INTO daily_data 
            (symbol, date, market_cap, price)
            VALUES (?, ?, ?, ?)
        """, daily_records)

        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error storing stock data: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    tickers = get_stock_universe()
    print(f"✅ Retrieved {len(tickers)} tickers.")

    stock_df = fetch_stock_data(tickers)
    print(stock_df)
    if stock_df.empty:
        print("⚠️ No data retrieved.")
        exit()
    
    store_stock_data(stock_df)
    print("✅ Data acquisition and storage complete.")


