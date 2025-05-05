import pandas as pd
import numpy as np
import json
from app.utils import get_redis_client
from app.database import get_db_connection
from datetime import date, timedelta, datetime

r = get_redis_client()

def replace_nan(obj):
    """Recursively replace NaN values with None."""
    if isinstance(obj, float) and (obj != obj):  # Check for NaN
        return None  # Replace with None or another placeholder
    elif isinstance(obj, dict):  # Handle nested dictionaries
        return {key: replace_nan(value) for key, value in obj.items()}
    elif isinstance(obj, list):  # Handle nested lists
        return [replace_nan(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, date, datetime)):  # Handle datetime objects
        return obj.isoformat()
    return obj

def default_serializer(obj):
    if isinstance(obj, (pd.Timestamp, date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, float) and (obj != obj):  # This checks for NaN (NaN is not equal to itself)
        return replace_nan(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def build_index_logic(conn, start_date, end_date):
    all_performance = []
    prev_index_value = None
    
    for current_date in pd.date_range(start_date, end_date, freq='B'):
        df = conn.execute(f"""
            SELECT dd.price, dd.market_cap, sm.symbol
            FROM daily_data dd
            JOIN stock_metadata sm ON dd.symbol = sm.symbol
            WHERE dd.date = '{current_date.date()}'
            ORDER BY dd.market_cap DESC
            LIMIT 100
        """).df()

        if df.empty or len(df) < 100:
            continue

        # Ensure no NaN values in the dataframe before performing any calculations
        df = df.fillna(0)

        df['weight'] = 1 / len(df)
        index_value = (df['price'] * df['weight']).sum()
        daily_return = None
        cumulative_return = None
        if prev_index_value is not None:
            daily_return = (index_value - prev_index_value) / prev_index_value
            cumulative_return = (1 + daily_return) * all_performance[-1]['cumulative_return']
        else:
            cumulative_return = 1.0

        performance = {
            'date': str(current_date.date()),  # Convert to str for JSON compatibility
            'index_value': index_value,
            'daily_return': daily_return,
            'cumulative_return': cumulative_return
        }

        all_performance.append(performance)

        conn.execute(
            "INSERT OR REPLACE INTO index_performance (date, index_value, daily_return, cumulative_return) VALUES (?, ?, ?, ?)",
            (performance['date'], index_value, daily_return, cumulative_return)
        )

        for _, row in df.iterrows():
            conn.execute(
                "INSERT OR REPLACE INTO index_composition (date, symbol, weight) VALUES (?, ?, ?)",
                (performance['date'], row['symbol'], row['weight'])
            )
        prev_index_value = index_value
    cleaned_performance = [replace_nan(perf) for perf in all_performance]
    r.set(f"index:{start_date}:{end_date}", json.dumps(cleaned_performance, default=default_serializer))
    return cleaned_performance
    


def get_index_performance(conn, start_date, end_date):
    cache_key = f"index:{start_date}:{end_date}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    df = conn.execute(f"""
        SELECT * FROM index_performance
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date
    """).df()
    records = df.to_dict(orient="records")

    # Use the default serializer to ensure proper NaN handling before storing in Redis
    cleaned_records = [replace_nan(record) for record in records]

    r.set(cache_key, json.dumps(cleaned_records, default=default_serializer))
    return cleaned_records

def get_index_composition(conn, date):
    key = f"composition:{date}"
    cached = r.get(key)
    if cached:
        return json.loads(cached)

    df = conn.execute(f"""
        SELECT ic.date, sm.symbol, ic.weight
        FROM index_composition ic
        JOIN stock_metadata sm ON ic.symbol = sm.symbol
        WHERE ic.date = '{date}'
    """).df()

    records = df.to_dict(orient="records")

    # Use the default serializer to ensure proper NaN handling before storing in Redis
    cleaned_records = [replace_nan(record) for record in records]

    r.set(key, json.dumps(cleaned_records, default=default_serializer))
    return cleaned_records

def get_composition_changes(conn, start_date, end_date):
    changes = []
    dates = pd.date_range(start_date, end_date, freq='B')
    prev_symbols = set()

    for d in dates:
        date = d.date()
        symbols = set(conn.execute(f"""
            SELECT sm.symbol
            FROM index_composition ic
            JOIN stock_metadata sm ON ic.symbol = sm.symbol
            WHERE ic.date = '{date}'
        """).df()['symbol'])

        entered = list(symbols - prev_symbols)
        exited = list(prev_symbols - symbols)

        if entered or exited:
            changes.append({
                'date': str(date),
                'entered': entered,
                'exited': exited
            })

        prev_symbols = symbols
    cleaned_changes = [replace_nan(change) for change in changes]

    r.set(f"changes:{start_date}:{end_date}", json.dumps(cleaned_changes, default=default_serializer))
    return cleaned_changes
