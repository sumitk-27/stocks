import json
import sqlite3
import requests
from rag_store import query_rag_catalysts

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

def save_prediction_to_db(ticker: str, pred: dict):
    if "error" in pred:
        return
    conn = sqlite3.connect("stocks_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (ticker, timestamp, direction, target_price_change_pct, confidence_score, reasoning)
        VALUES (?, datetime('now'), ?, ?, ?, ?)
    """, (
        ticker,
        pred.get("direction", "NEUTRAL"),
        pred.get("target_price_change_pct", 0.0),
        pred.get("confidence_score", 0.0),
        pred.get("reasoning", "")
    ))
    conn.commit()
    conn.close()
    print(f"✅ Saved prediction for {ticker} into database.")

def generate_stock_prediction(ticker: str) -> dict:
    catalysts = query_rag_catalysts(ticker, query="earnings growth momentum", top_k=3)
    catalyst_text = "\n".join([f"- {c['content']}" for c in catalysts]) if catalysts else "No recent breaking news."

    prompt = f"""
    Analyze {ticker} with these catalysts:
    {catalyst_text}

    Return JSON only:
    {{
        "ticker": "{ticker}",
        "direction": "BULLISH",
        "target_price_change_pct": 2.5,
        "confidence_score": 0.85,
        "reasoning": "Strong momentum and catalyst support."
    }}
    """

    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False, "format": "json"}

    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=300)
        data = json.loads(res.json().get("response", "{}"))
        save_prediction_to_db(ticker, data)
        return data
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("Generating test prediction for RELIANCE.NS...")
    result = generate_stock_prediction("RELIANCE.NS")
    print(json.dumps(result, indent=2))