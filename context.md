# Project Context: AI-Driven Indian Stock Market & Intraday Dashboard

## 1. Executive Summary
Building a local-first, AI-powered stock market analysis and prediction platform for Indian equities (NSE/BSE). Styled after Moneycontrol, the platform integrates historical price databases, technical indicator algorithms, live breaking news scraping, a ChromaDB vector RAG store, and a local Ollama LLM to manage user watchlists, render candlestick charts, track portfolios, and generate automated 9:00 AM and 9:00 PM IST top intraday/swing mover predictions.

## 2. Technical Stack
* **UI & Visualization:** Streamlit, Plotly (Interactive Candlestick & Technical Overlay Charts)
* **Local LLM Engine:** Ollama (`llama3.2`)
* **Protocol Standard:** Model Context Protocol (MCP) via `mcp.server.mcpserver` (MCP v2.x compliant)
* **Relational Database:** SQLite (`stocks_history.db`) for daily OHLCV price history and timestamped AI prediction snapshots
* **Vector Database (RAG):** ChromaDB (`./chroma_news_db`) using SentenceTransformer embeddings for news catalyst matching
* **Data Retrieval & Web Scraping:** `yfinance` (auto-routing `.NS` for NSE and `.BO` for BSE), `feedparser` (Google News RSS feeds)
* **Technical Analysis Engine:** `ta` / `pandas-ta` (RSI, VWAP, Supertrend, MACD, 50/200 EMAs)
* **Automation & Scheduling:** `APScheduler` (Cron triggers configured for `Asia/Kolkata` at 09:00 AM and 21:00 PM IST)

## 3. Project Directory Structure
```text
stocks/
├── __pycache__/            # Python bytecode cache
├── venv/                   # Active Python Virtual Environment
├── chroma_news_db/         # ChromaDB persistent vector database directory
├── context.md              # Project source of truth & progress tracking
├── config.py               # Environment configuration switcher (LOCAL vs GCP)
├── init_db.py              # SQLite table initialization script
├── ingest_history.py       # Batch OHLCV price history downloader (2020–yesterday)
├── server.py               # MCP v2 Server exposing Indian equity data tools
├── test_server.py          # Verification suite for MCP tools and yfinance
├── news_engine.py          # Live news fetcher and RSS scraper module
├── rag_store.py            # ChromaDB news embedding & RAG semantic search engine
├── predictor.py            # Ollama catalyst analysis & top-mover predictor
├── scheduler_service.py    # Background cron service for 9 AM & 9 PM market scans
├── app.py                  # Streamlit dashboard UI (Moneycontrol-style interface)
├── stocks_history.db       # SQLite relational database
└── requirements.txt        # Python dependency manifest