from server import get_stock_price, get_historical_summary

def test_mcp_tools():
    print("--- Testing get_stock_price ---")
    price_res = get_stock_price("RELIANCE")
    print(price_res)

    print("\n--- Testing get_historical_summary ---")
    hist_res = get_historical_summary("TCS", period="1mo")
    print(hist_res)

if __name__ == "__main__":
    test_mcp_tools()