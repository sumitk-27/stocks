import os
import requests
import pandas as pd

# Set ENVIRONMENT to 'GCP' when deploying to Cloud Run / Compute Engine
ENVIRONMENT = os.getenv("ENVIRONMENT", "LOCAL")

# Core 10-stock test array for local rapid prototyping
LOCAL_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS",
    "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "LT.NS", "AXISBANK.NS"
]

def get_target_tickers() -> list[str]:
    """
    Returns local 10-stock list in LOCAL mode, 
    or dynamically fetches full Nifty 500 / NSE master list in GCP mode.
    """
    if ENVIRONMENT == "LOCAL":
        return LOCAL_TICKERS
    
    # GCP Mode: Fetch full Nifty 500 list directly from NSE source
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {"User-Agent": "Mozilla/5.0"}
        df = pd.read_csv(url)
        # Convert NSE symbols (e.g. RELIANCE) to yfinance format (RELIANCE.NS)
        gcp_tickers = [f"{symbol.strip()}.NS" for symbol in df["Symbol"].dropna()]
        return gcp_tickers
    except Exception as e:
        print(f"Error fetching full market list on GCP, falling back to local: {e}")
        return LOCAL_TICKERS