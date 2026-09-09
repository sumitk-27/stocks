import sqlite3

def init_prediction_tables():
    conn = sqlite3.connect("stocks_history.db")
    cursor = conn.cursor()
    
    # Stores daily 9AM and 9PM snapshot predictions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_top10_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        slot TEXT,             -- '9AM_PRE_MARKET' or '9PM_POST_MARKET'
        prediction_date TEXT,  -- e.g., '2026-09-07'
        top_stocks_json TEXT,  -- JSON string containing the 10 selected stocks & reasoning
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_prediction_tables()
    print("Prediction database table ready.")