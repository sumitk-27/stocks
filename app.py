import sqlite3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import get_target_tickers
from news_engine import fetch_stock_news
from predictor import generate_stock_prediction
from rag_store import query_rag_catalysts

# Page Configuration
st.set_page_config(
    page_title="Indian Equity Intelligence Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Moneycontrol-style clean UI & High-Contrast Prediction Cards
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e2638 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    .prediction-hero-bullish {
        background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
        border: 2px solid #10b981;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .prediction-hero-bearish {
        background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%);
        border: 2px solid #ef4444;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .prediction-hero-neutral {
        background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
        border: 2px solid #9ca3af;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .badge-bullish { background-color: #10b981; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
    .badge-bearish { background-color: #ef4444; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
    .badge-neutral { background-color: #6b7280; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: bold; }
</style>
""", unsafe_allow_cookies=True, unsafe_allow_html=True)

# Session State Initialization for Watchlist & Portfolio
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"ticker": "RELIANCE.NS", "qty": 10, "buy_price": 1350.0},
        {"ticker": "INFY.NS", "qty": 25, "buy_price": 1820.0}
    ]

# Helper Database Functions
def load_price_data(ticker: str) -> pd.DataFrame:
    conn = sqlite3.connect("stocks_history.db")
    df = pd.read_sql_query(
        "SELECT * FROM stock_prices WHERE ticker = ? ORDER BY date ASC",
        conn, params=(ticker,)
    )
    conn.close()
    return df

def get_latest_prediction(ticker: str):
    conn = sqlite3.connect("stocks_history.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, direction, target_price_change_pct, confidence_score, reasoning FROM predictions WHERE ticker = ? ORDER BY id DESC LIMIT 1",
        (ticker,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "timestamp": row[0],
            "direction": row[1],
            "target_price_change_pct": row[2],
            "confidence_score": row[3],
            "reasoning": row[4]
        }
    return None

def save_prediction_to_db(ticker: str, pred: dict):
    if "error" in pred:
        return
    conn = sqlite3.connect("stocks_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (ticker, timestamp, direction, target_price_change_pct, confidence_score, reasoning)
        VALUES (?, datetime('now'), ?, ?, ?, ?)
    """, (
        ticker,
        pred.get("direction", "NEUTRAL"),
        pred.get("target_price_change_pct", 0.0),
        pred.get("confidence_score", 0.0),
        pred.get("reasoning", "")
    ))
    conn.commit()
    conn.close()

# --- SIDEBAR: Watchlist & Portfolio Navigation ---
st.sidebar.title("📌 Market Terminal")

# Watchlist Manager
st.sidebar.subheader("⭐ My Watchlist")
for w_ticker in st.session_state.watchlist:
    col_w1, col_w2 = st.sidebar.columns([3, 1])
    if col_w1.button(f"🔍 {w_ticker}", key=f"btn_w_{w_ticker}"):
        st.session_state.selected_ticker = w_ticker
    if col_w2.button("❌", key=f"del_w_{w_ticker}"):
        st.session_state.watchlist.remove(w_ticker)
        st.rerun()

# --- MAIN HEADER: Universal Search Bar ---
all_tickers = get_target_tickers()
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = all_tickers[0]

st.title("⚡ Indian Equity Intelligence Terminal")

search_col1, search_col2 = st.columns([4, 1])
with search_col1:
    selected = st.selectbox(
        "🔍 Search Indian Equities (NSE/BSE)...",
        options=all_tickers,
        index=all_tickers.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in all_tickers else 0
    )
    st.session_state.selected_ticker = selected

with search_col2:
    st.write("")
    st.write("")
    if st.button("➕ Add to Watchlist"):
        if selected not in st.session_state.watchlist:
            st.session_state.watchlist.append(selected)
            st.success(f"Added {selected}")
            st.rerun()

current_ticker = st.session_state.selected_ticker

# Fetch Data
price_df = load_price_data(current_ticker)
pred = get_latest_prediction(current_ticker)

# --- SECTION 1: HIGHLIGHTED HERO AI PREDICTION CARD ---
st.subheader(f"🤖 AI Quant Prediction Hub — {current_ticker}")

if pred:
    direction = pred.get("direction", "NEUTRAL").upper()
    css_class = "prediction-hero-bullish" if direction == "BULLISH" else ("prediction-hero-bearish" if direction == "BEARISH" else "prediction-hero-neutral")
    badge_class = "badge-bullish" if direction == "BULLISH" else ("badge-bearish" if direction == "BEARISH" else "badge-neutral")

    st.markdown(f"""
    <div class="{css_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin: 0;">Market Outlook: <span class="{badge_class}">{direction}</span></h2>
            <p style="margin: 0; color: #9ca3af;">Last Snapshot: {pred['timestamp']}</p>
        </div>
        <hr style="border-color: #4b5563; margin: 15px 0;">
        <div style="display: flex; gap: 40px;">
            <div>
                <p style="margin: 0; color: #9ca3af; font-size: 14px;">Target Price Move</p>
                <h1 style="margin: 0; font-size: 32px;">{pred['target_price_change_pct']}%</h1>
            </div>
            <div>
                <p style="margin: 0; color: #9ca3af; font-size: 14px;">Confidence Score</p>
                <h1 style="margin: 0; font-size: 32px;">{pred['confidence_score'] * 100:.0f}%</h1>
            </div>
        </div>
        <div style="margin-top: 15px;">
            <p style="margin: 0; color: #9ca3af; font-size: 14px;">Catalyst & Technical Reasoning:</p>
            <p style="font-size: 16px; margin-top: 5px; line-height: 1.5;">{pred['reasoning']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("ℹ️ No saved AI prediction snapshot available for this stock.")

col_btn1, col_btn2 = st.columns([2, 3])
with col_btn1:
    if st.button("🚀 Generate On-Demand AI Prediction (Ollama + RAG)", type="primary"):
        with st.spinner("Analyzing price action & running RAG news engine..."):
            new_pred = generate_stock_prediction(current_ticker)
            if "error" not in new_pred:
                save_prediction_to_db(current_ticker, new_pred)
                st.success("Prediction updated!")
                st.rerun()
            else:
                st.error(f"Prediction failed: {new_pred['error']}")

# --- SECTION 2: MONEYCONTROL-STYLE TABS ---
tab_charts, tab_portfolio, tab_news = st.tabs(["📈 Technical Charts", "💼 Portfolio Tracker", "📰 News Catalysts (RAG)"])

with tab_charts:
    if not price_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=price_df['date'],
            open=price_df['open'],
            high=price_df['high'],
            low=price_df['low'],
            close=price_df['close'],
            name="OHLC"
        ))
        fig.update_layout(
            title=f"{current_ticker} Price Action (Interactive Candlestick)",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No price history available in `stocks_history.db`. Run `python ingest_history.py`.")

with tab_portfolio:
    st.subheader("💼 Portfolio & Positions Tracker")
    
    with st.expander("➕ Add Position"):
        with st.form("add_portfolio_form"):
            port_ticker = st.selectbox("Stock", all_tickers)
            port_qty = st.number_input("Shares Quantity", min_value=1, value=10)
            port_price = st.number_input("Buy Price (₹)", min_value=0.1, value=1000.0)
            submitted = st.form_submit_button("Add Position")
            if submitted:
                st.session_state.portfolio.append({"ticker": port_ticker, "qty": port_qty, "buy_price": port_price})
                st.success(f"Added {port_qty} shares of {port_ticker}")
                st.rerun()

    if st.session_state.portfolio:
        port_df = pd.DataFrame(st.session_state.portfolio)
        st.dataframe(port_df, use_container_width=True)
    else:
        st.info("Your portfolio is currently empty.")

with tab_news:
    st.subheader("📰 Live News & RAG Context")
    news_items = fetch_stock_news(current_ticker, max_results=5)
    for n in news_items:
        st.markdown(f"**[{n['title']}]({n['link']})**")
        st.caption(f"Published: {n['published']}")
        st.write("---")