import sqlite3
import json
import requests
from datetime import datetime
from config import get_target_tickers
from news_engine import fetch_market_news_batch
from rag_store import ingest_articles_to_rag, query_rag_catalysts

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

def get_recent_ohlcv_summary(ticker: str, limit: int = 5) -> dict:
    """Retrieves recent OHLCV rows from SQLite daily_prices table."""
    conn = sqlite3.connect("stocks_history.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, open, high, low, close, volume 
        FROM daily_prices 
        WHERE ticker = ? 
        ORDER BY date DESC LIMIT ?
    """, (ticker, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {}
        
    latest = rows[0]
    return {
        "latest_date": latest[0],
        "close": latest[4],
        "open": latest[1],
        "volume": latest[5]
    }

def generate_predictions(slot: str = "9AM_PRE_MARKET") -> dict:
    """
    Runs full RAG pipeline and queries Ollama to rank equity movers.
    """
    tickers = get_target_tickers()
    
    # 1. Scrape & Ingest News into ChromaDB
    print("Fetching and embedding market catalysts...")
    news_batch = fetch_market_news_batch(tickers, max_per_ticker=2)
    all_articles = [art for news in news_batch.values() for art in news]
    ingest_articles_to_rag(all_articles)
    
    # 2. Build Context per Stock
    market_context = []
    for ticker in tickers:
        price_data = get_recent_ohlcv_summary(ticker)
        rag_hits = query_rag_catalysts(ticker, top_k=2)
        news_summaries = [h["content"] for h in rag_hits]
        
        market_context.append({
            "ticker": ticker,
            "latest_price": price_data.get("close", "N/A"),
            "latest_volume": price_data.get("volume", "N/A"),
            "news_catalysts": news_summaries
        })
        
    # 3. Formulate Prompt for Llama 3.2
    prompt = f"""
You are an expert Indian stock market intraday and swing trading analyst.
Slot: {slot}
Current Context:
{json.dumps(market_context, indent=2)}

Task: Analyze the provided price/volume context and news catalysts. 
Select top high-conviction movers for intraday/swing trades.

Respond strictly in valid JSON with key "predictions" containing an array of objects:
[
  {{
    "ticker": "SYMBOL.NS",
    "signal": "BULLISH" | "BEARISH",
    "rationale": "Short concise catalyst breakdown",
    "confidence_score": 0.85
  }}
]
"""

    # 4. Query Ollama
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        result = response.json()
        prediction_data = json.loads(result.get("response", "{}"))
        
        # 5. Persist snapshot to SQLite
        save_prediction_snapshot(slot, prediction_data)
        return prediction_data

    except Exception as e:
        print(f"Prediction generation failed: {e}")
        return {"error": str(e)}

def save_prediction_snapshot(slot: str, prediction_json: dict):
    conn = sqlite3.connect("stocks_history.db")
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO daily_top10_predictions (timestamp, slot, prediction_date, top_stocks_json)
        VALUES (?, ?, ?, ?)
    """, (timestamp_str, slot, today_str, json.dumps(prediction_json)))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Running test prediction cycle...")
    preds = generate_predictions("9AM_PRE_MARKET")
    print(json.dumps(preds, indent=2))