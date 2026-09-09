import yfinance as yf
from mcp.server.mcpserver import MCPServer

# Initialize MCPServer for Indian Equities
mcp = MCPServer("Indian Stock Analysis Server")

def sanitize_indian_ticker(ticker: str) -> str:
    """Helper to ensure ticker is correctly formatted for Indian exchanges (defaulting to NSE)."""
    ticker = ticker.strip().upper()
    if not (ticker.endswith(".NS") or ticker.endswith(".BO") or ticker.startswith("^")):
        return f"{ticker}.NS"
    return ticker

@mcp.tool()
def get_stock_price(ticker: str) -> dict:
    """Fetch current stock price and key financial metrics for an Indian stock (e.g., RELIANCE, TCS, INFY, HDFCBANK)."""
    formatted_ticker = sanitize_indian_ticker(ticker)
    stock = yf.Ticker(formatted_ticker)
    info = stock.info
    
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    if not current_price:
        return {"error": f"Could not retrieve price for {formatted_ticker}. Verify symbol."}

    return {
        "symbol": formatted_ticker,
        "company_name": info.get("longName") or info.get("shortName"),
        "current_price_inr": current_price,
        "currency": "INR",
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
        "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
        "marketCap_inr": info.get("marketCap"),
        "peRatio": info.get("trailingPE"),
    }

@mcp.tool()
def get_historical_summary(ticker: str, period: str = "1mo") -> dict:
    """Fetch historical performance summary for Indian stocks. Period options: 1mo, 3mo, 6mo, 1y, 5y."""
    formatted_ticker = sanitize_indian_ticker(ticker)
    stock = yf.Ticker(formatted_ticker)
    hist = stock.history(period=period)
    
    if hist.empty:
        return {"error": f"No historical data found for {formatted_ticker}"}
        
    start_price = float(hist["Close"].iloc[0])
    end_price = float(hist["Close"].iloc[-1])
    pct_change = ((end_price - start_price) / start_price) * 100
    
    return {
        "ticker": formatted_ticker,
        "period": period,
        "start_price_inr": round(start_price, 2),
        "latest_price_inr": round(end_price, 2),
        "percentage_change": round(pct_change, 2),
        "avg_daily_volume": int(hist["Volume"].mean()),
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")