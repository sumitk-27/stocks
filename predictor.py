import json
import requests
from config import get_target_tickers
from rag_store import query_rag_catalysts

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

def generate_stock_prediction(ticker: str, timeout_seconds: int = 300) -> dict:
    """
    Queries local Ollama instance with RAG catalysts to generate 
    intraday/swing predictions with an extended timeout.
    """
    # Fetch RAG catalysts from ChromaDB
    catalysts = query_rag_catalysts(ticker, query="earnings momentum sentiment breakout catalyst", top_k=3)
    catalyst_text = "\n".join([f"- {c['content']}" for c in catalysts]) if catalysts else "No recent breaking catalysts found."

    prompt = f"""
    You are an expert Indian Stock Market Quantitative Analyst.
    Analyze the following stock ticker and recent news catalysts:

    Ticker: {ticker}
    Recent Catalysts:
    {catalyst_text}

    Provide a concise intraday prediction in valid JSON format with keys:
    "ticker", "direction" ("BULLISH"/"BEARISH"/"NEUTRAL"), "target_price_change_pct", "confidence_score", "reasoning".
    Return ONLY valid raw JSON.
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        # Set explicitly extended timeout (300 seconds)
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        
        result_json = response.json()
        response_text = result_json.get("response", "{}")
        return json.loads(response_text)
    except requests.exceptions.Timeout:
        print(f"⚠️ Ollama request timed out for {ticker} after {timeout_seconds}s.")
        return {"error": f"Ollama timeout after {timeout_seconds}s"}
    except Exception as e:
        print(f"❌ Error generating prediction for {ticker}: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("Running test prediction cycle...")
    print("Fetching and embedding market catalysts...")
    
    # Test on primary sample ticker
    sample_ticker = "RELIANCE.NS"
    prediction = generate_stock_prediction(sample_ticker)
    
    print("\n--- Ollama Prediction Output ---")
    print(json.dumps(prediction, indent=2))