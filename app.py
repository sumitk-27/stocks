import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import json
from config import get_target_tickers
from rag_store import query_rag_catalysts

st.set_page_config(page_title="Indian Equity Intelligence", layout="wide")

st.title("📈 Indian Equity Intelligence & RAG Prediction Engine")

# Sidebar Controls
tickers = get_target_tickers()
selected_ticker = st.sidebar.selectbox("Select Stock Ticker", tickers)

# Main Grid Layout
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader(f"Price Action — {selected_ticker}")
    conn = sqlite3.connect("stocks_history.db")
    df = pd.read_sql_query(
        "SELECT date, open, high, low, close, volume FROM daily_prices WHERE ticker = ? ORDER BY date ASC",
        conn,
        params=(selected_ticker,)
    )
    conn.close()

    if not df.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df['date'], open=df['open'], high=df['high'],
            low=df['low'], close=df['close'], name=selected_ticker
        )])
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=420)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No price history found in database.")

with col_right:
    st.subheader("🤖 Latest AI Prediction Snapshot")
    conn = sqlite3.connect("stocks_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, slot, top_stocks_json FROM daily_top10_predictions ORDER BY id DESC LIMIT 1")
    last_pred = cursor.fetchone()
    conn.close()

    if last_pred:
        ts, slot, data_str = last_pred
        st.caption(f"Last Run: {ts} | Slot: {slot}")
        try:
            preds = json.loads(data_str).get("predictions", [])
            ticker_pred = next((p for p in preds if p.get("ticker") == selected_ticker), None)
            
            if ticker_pred:
                signal = ticker_pred.get("signal", "NEUTRAL")
                color = "green" if signal == "BULLISH" else "red" if signal == "BEARISH" else "orange"
                st.markdown(f"### Signal: :{color}[{signal}]")
                st.write(f"**Confidence Score:** {ticker_pred.get('confidence_score', 'N/A')}")
                st.write(f"**Rationale:** {ticker_pred.get('rationale', 'N/A')}")
            else:
                st.info("Ticker not highlighted in the top conviction list for this snapshot.")
        except Exception:
            st.error("Failed to parse prediction output.")
    else:
        st.write("No prediction snapshot available.")

# Vector News Feed
st.divider()
st.subheader("📰 RAG Vector-Matched News Catalysts")
catalysts = query_rag_catalysts(selected_ticker, top_k=3)

if catalysts:
    for cat in catalysts:
        meta = cat.get("metadata", {})
        with st.expander(f"📌 {meta.get('title', 'News Item')} ({meta.get('published', 'N/A')})"):
            st.write(cat.get("content"))
            if meta.get("link"):
                st.markdown(f"[Read Full Source]({meta.get('link')})")
else:
    st.write("No vector-indexed news catalysts found for this ticker.")