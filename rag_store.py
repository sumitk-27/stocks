import chromadb
from chromadb.config import Settings

CHROMA_PATH = "./chroma_news_db"

def get_chroma_collection():
    """Initializes persistent ChromaDB client and returns the news collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(name="stock_news")

def ingest_articles_to_rag(articles: list[dict]) -> int:
    """
    Upserts structured news articles into ChromaDB using default embeddings.
    """
    if not articles:
        return 0

    collection = get_chroma_collection()
    documents = []
    metadatas = []
    ids = []

    for idx, art in enumerate(articles):
        # Unique ID based on ticker and link
        art_id = f"{art['ticker']}_{hash(art['link'])}"
        text_content = f"Title: {art['title']}\nSummary: {art['summary']}"
        
        documents.append(text_content)
        metadatas.append({
            "ticker": art["ticker"],
            "title": art["title"],
            "link": art["link"],
            "published": art["published"]
        })
        ids.append(art_id)

    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    return len(documents)

def query_rag_catalysts(ticker: str, query: str = "earnings momentum growth catalyst", top_k: int = 3) -> list[dict]:
    """
    Performs semantic vector search against stored news articles for a target ticker.
    """
    collection = get_chroma_collection()
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"ticker": ticker}
    )

    matched_news = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results else []
        
        for doc, meta in zip(docs, metas):
            matched_news.append({
                "content": doc,
                "metadata": meta
            })
            
    return matched_news

if __name__ == "__main__":
    from news_engine import fetch_stock_news
    
    print("Testing RAG Ingestion for RELIANCE.NS...")
    sample_news = fetch_stock_news("RELIANCE.NS", max_results=3)
    count = ingest_articles_to_rag(sample_news)
    print(f"Ingested {count} articles into ChromaDB.")
    
    matches = query_rag_catalysts("RELIANCE.NS", "growth expansion profit")
    print(f"Found {len(matches)} RAG semantic matches.")