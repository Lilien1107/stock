import pandas as pd
import pytz
import yfinance as yf
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="My Stock Monitor", page_icon="📈", layout="wide")

# ---- 固定追蹤的股票 ----
TICKERS = [
    "CVX", "VZ", "T", "STLD", "NUE", "FDX", "JNJ", "O", "MO", "PM", "TSLA", "WMT",
    "META", "JPM", "TSM", "GOOGL", "ORCL", "AXP", "NFLX", "AAPL", "SPY", "AMZN",
    "NVDA", "KO", "COST", "SBUX"
]

et = pytz.timezone("US/Eastern")
now_et = datetime.now(et)

@st.cache_data(ttl=300)  # 緩存5分鐘
def fetch_one(ticker: str):
    t = yf.Ticker(ticker)
    hist = t.history(period="1y", auto_adjust=False)
    if hist.empty:
        return None

    wk52_high = float(hist["High"].max())
    wk52_low = float(hist["Low"].min())
    wk52_avg = float(hist["Close"].mean())

    intraday = t.history(period="1d", interval="1m")
    if not intraday.empty:
        current = float(intraday["Close"].iloc[-1])
    else:
        current = float(t.fast_info.get("last_price") or hist["Close"].iloc[-1])

    return {
        "ticker": ticker.upper(),
        "now": current,
        "52w_high": wk52_high,
        "52w_low": wk52_low,
        "52w_avg": wk52_avg,
        "history": hist["Close"],
    }

def fmt(v):
    return f"${v:,.2f}"

st.title("📈 My Stock Monitor")
st.caption("資料來源：Yahoo Finance (約 15 分鐘延遲)")

rows = []
charts = {}

for t in TICKERS:
    data = fetch_one(t)
    if not data:
        st.warning(f"⚠️ {t}: 無法取得資料")
        continue
    rows.append(
        {
            "Ticker": data["ticker"],
            "Now": data["now"],
            "52w High": data["52w_high"],
            "52w Low": data["52w_low"],
            "52w Avg": data["52w_avg"],
            "% from Avg": (data["now"] / data["52w_avg"] - 1.0) * 100,
            "% to High": (data["now"] / data["52w_high"] - 1.0) * 100,
        }
    )
    charts[data["ticker"]] = data["history"]

if rows:
    df = pd.DataFrame(rows).sort_values("% from Avg")
    styled = (
        df.style
        .format({"Now": fmt, "52w High": fmt, "52w Low": fmt, "52w Avg": fmt,
                 "% from Avg": "{:+.2f}%", "% to High": "{:+.2f}%"})
    )
    st.subheader(f"更新時間 / Updated: {now_et:%Y-%m-%d %H:%M:%S %Z}")
    st.dataframe(styled, use_container_width=True)

    st.subheader("一年收盤走勢 / 1-year Close")
    cols = st.columns(2)
    i = 0
    for tk, s in charts.items():
        with cols[i % 2]:
            st.markdown(f"**{tk}**")
            st.line_chart(s)
        i += 1
