import os
import time
import tarfile
import requests
import chromadb

CHROMA_PATH = "./chroma_news_db"
MODEL_URL = "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"
CACHE_DIR = os.path.expanduser(os.path.join("~", ".cache", "chroma", "onnx_models", "all-MiniLM-L6-v2"))
TAR_PATH = os.path.join(CACHE_DIR, "onnx.tar.gz")

def ensure_onnx_model_downloaded():
    """
    Pre-downloads the Chroma ONNX model with HTTP Range support (resumable download)
    and an extended timeout to prevent internal httpx ConnectTimeout/ReadTimeout errors.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Skip if file is already complete (>75 MB)
    if os.path.exists(TAR_PATH) and os.path.getsize(TAR_PATH) > 75 * 1024 * 1024:
        return

    print("📥 Resuming/Pre-downloading ONNX model with extended timeout...")
    existing_size = os.path.getsize(TAR_PATH) if os.path.exists(TAR_PATH) else 0
    headers = {"Range": f"bytes={existing_size}-"} if existing_size > 0 else {}
    mode = "ab" if existing_size > 0 else "wb"

    try:
        res = requests.get(MODEL_URL, headers=headers, stream=True, timeout=300)
        if res.status_code in (200, 206):
            total_bytes = int(res.headers.get("content-length", 0)) + existing_size
            downloaded = existing_size
            with open(TAR_PATH, mode) as f:
                for chunk in res.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        pct = (downloaded / total_bytes) * 100 if total_bytes else 0
                        print(f" Progress: {downloaded / (1024*1024):.2f} MB / {total_bytes / (1024*1024):.2f} MB ({pct:.1f}%)", end="\r")
            print("\n✅ Model downloaded successfully.")
        else:
            res = requests.get(MODEL_URL, stream=True, timeout=300)
            with open(TAR_PATH, "wb") as f:
                for chunk in res.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            print("\n✅ Model downloaded successfully.")
            
        if os.path.exists(TAR_PATH):
            with tarfile.open(TAR_PATH, "r:gz") as tar:
                tar.extractall(path=CACHE_DIR)
    except Exception as e:
        print(f"\n⚠️ Resumable download warning: {e}. Proceeding to ChromaDB initialization...")

def get_chroma_collection(max_retries: int = 5, backoff_factor: int = 3):
    """
    Ensures model pre-downloading and initializes ChromaDB collection.
    """
    ensure_onnx_model_downloaded()
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    for attempt in range(1, max_retries + 1):
        try:
            collection = client.get_or_create_collection(name="stock_news")
            collection.count()
            return collection
        except Exception as e:
            if attempt == max_retries:
                print(f"❌ Failed to initialize ChromaDB after {max_retries} attempts.")
                raise e
            wait_time = attempt * backoff_factor
            print(f"⚠️ Chroma DB access issue (Attempt {attempt}/{max_retries}). Retrying in {wait_time}s...")
            time.sleep(wait_time)

def ingest_articles_to_rag(articles: list[dict], max_retries: int = 5) -> int:
    """
    Upserts structured news articles into ChromaDB with retry logic.
    """
    if not articles:
        return 0

    documents = []
    metadatas = []
    ids = []

    for art in articles:
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

    for attempt in range(1, max_retries + 1):
        try:
            collection = get_chroma_collection()
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return len(documents)
        except Exception as e:
            if attempt == max_retries:
                print(f"❌ Failed to upsert documents into RAG store.")
                raise e
            wait_time = attempt * 3
            print(f"⚠️ Upsert issue (Attempt {attempt}/{max_retries}). Retrying in {wait_time}s...")
            time.sleep(wait_time)

def query_rag_catalysts(ticker: str, query: str = "earnings momentum growth catalyst", top_k: int = 3) -> list[dict]:
    """
    Performs semantic vector search against stored news articles for a target ticker.
    """
    try:
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
    except Exception as e:
        print(f"Error querying RAG store: {e}")
        return []

if __name__ == "__main__":
    from news_engine import fetch_stock_news
    
    print("Testing resilient RAG Ingestion for RELIANCE.NS...")
    sample_news = fetch_stock_news("RELIANCE.NS", max_results=3)
    count = ingest_articles_to_rag(sample_news)
    print(f"✅ Successfully ingested {count} articles into ChromaDB.")
    
    matches = query_rag_catalysts("RELIANCE.NS", "growth expansion profit")
    print(f"Found {len(matches)} RAG semantic matches.")