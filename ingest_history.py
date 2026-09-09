import sqlite3
import yfinance as yf
from datetime import datetime, timedelta

# Target liquid Indian stocks
TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS",
    "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "LT.NS", "AXISBANK.NS"
]

START_DATE = "2020-01-01"
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def init_tables(conn):
    """Ensures required tables exist in SQLite before inserting data."""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_prices (
        ticker TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        PRIMARY KEY (ticker, date)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_top10_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        slot TEXT,
        prediction_date TEXT,
        top_stocks_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

def populate_historical_prices():
    conn = sqlite3.connect("stocks_history.db")
    init_tables(conn)  # Automatically create tables if missing
    cursor = conn.cursor()
    
    print(f"Starting ingestion ({START_DATE} to {YESTERDAY})...", flush=True)
    
    for ticker in TICKERS:
        print(f"Fetching {ticker}...", end=" ", flush=True)
        try:
            data = yf.download(ticker, start=START_DATE, end=YESTERDAY, interval="1d", progress=False)
            
            if data.empty:
                print("No data found.", flush=True)
                continue

            if isinstance(data.columns, tuple) or getattr(data.columns, 'nlevels', 1) > 1:
                data.columns = data.columns.get_level_values(0)

            data.reset_index(inplace=True)
            
            records = []
            for _, row in data.iterrows():
                date_val = row["Date"]
                date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)[:10]
                
                records.append((
                    ticker,
                    date_str,
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    int(row["Volume"])
                ))
            
            cursor.executemany("""
            INSERT OR REPLACE INTO daily_prices (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, records)
            
            conn.commit()
            print(f"Saved {len(records)} rows.", flush=True)

        except Exception as e:
            print(f"Error: {e}", flush=True)

    conn.close()
    print("Database population finished successfully!", flush=True)

if __name__ == "__main__":
    populate_historical_prices()