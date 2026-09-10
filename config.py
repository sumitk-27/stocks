import os
import requests
import pandas as pd

ENVIRONMENT = os.getenv("ENVIRONMENT", "LOCAL")

# Core 10-stock test array for local rapid prototyping
LOCAL_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS",
    "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "LT.NS", "AXISBANK.NS"
]

def get_target_tickers() -> list[str]:
    """
    Returns local 10-stock list in LOCAL mode, 
    or dynamically fetches full NSE & BSE master lists in GCP mode.
    """
    if ENVIRONMENT == "LOCAL":
        return LOCAL_TICKERS
    
    tickers = []
    
    # GCP Mode: Fetch full NSE equities master list
    try:
        url_nse = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url_nse, headers=headers, timeout=10)
        if res.status_code == 200:
            df_nse = pd.read_csv(pd.io.common.BytesIO(res.content))
            tickers.extend([f"{symbol.strip()}.NS" for symbol in df_nse["SYMBOL"].dropna()])
    except Exception as e:
        print(f"Error fetching NSE list, trying Nifty 500 fallback: {e}")
        try:
            url_nifty = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
            df_nifty = pd.read_csv(url_nifty)
            tickers.extend([f"{symbol.strip()}.NS" for symbol in df_nifty["Symbol"].dropna()])
        except Exception as ex:
            print(f"Error fetching fallback Nifty list: {ex}")

    # GCP Mode: Fetch BSE equities master list
    try:
        url_bse = "https://api.bseindia.com/BseIndiaAPI/api/ListofScrip/w?Group=&Scrip_code=&scrip_name=&segment=Equity&status=Active"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url_bse, headers=headers, timeout=10)
        if res.status_code == 200:
            bse_data = res.json()
            tickers.extend([f"{item['SCRIP_CD'].strip()}.BO" for item in bse_data if 'SCRIP_CD' in item])
    except Exception as e:
        print(f"Error fetching BSE master list: {e}")

    # Deduplicate and return complete list
    all_tickers = sorted(list(set(tickers)))
    return all_tickers if all_tickers else LOCAL_TICKERS