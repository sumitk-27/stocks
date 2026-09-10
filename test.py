# Save and run as fix_db.py
import sqlite3

conn = sqlite3.connect("stocks_history.db")
cursor = conn.cursor()

# Create predictions table if missing
cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    direction TEXT,
    target_price_change_pct REAL,
    confidence_score REAL,
    reasoning TEXT
)
""")

conn.commit()
conn.close()
print("✅ Database schema updated with predictions table.")