import feedparser
import urllib.parse
from datetime import datetime

def fetch_stock_news(ticker: str, max_results: int = 5) -> list[dict]:
    """
    Scrapes live Google News RSS feeds for a target Indian stock ticker.
    """
    clean_symbol = ticker.replace(".NS", "").replace(".BO", "")
    query = f"{clean_symbol} stock news india"
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    feed = feedparser.parse(rss_url)
    articles = []
    
    for entry in feed.entries[:max_results]:
        articles.append({
            "ticker": ticker,
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
            "summary": entry.get("summary", entry.get("title", ""))
        })
        
    return articles

def fetch_market_news_batch(tickers: list[str], max_per_ticker: int = 3) -> dict[str, list[dict]]:
    """Fetches breaking news articles across a batch of stock tickers."""
    batch_news = {}
    for ticker in tickers:
        batch_news[ticker] = fetch_stock_news(ticker, max_results=max_per_ticker)
    return batch_news

if __name__ == "__main__":
    print("Testing news engine for RELIANCE.NS...")
    news_items = fetch_stock_news("RELIANCE.NS", max_results=3)
    for idx, item in enumerate(news_items, 1):
        print(f"\n[{idx}] {item['title']}\n    Published: {item['published']}\n    Link: {item['link']}")