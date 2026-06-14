import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
import os

st.set_page_config(page_title="주식 분석", layout="wide", page_icon="📈")

st.markdown("""
<style>
    .main { background-color: #0F0F0F; color: #EDEDED; }
    .stApp { background-color: #0F0F0F; }
    h1 { color: #00C4B4; font-weight: bold; font-size: 1.8rem; }
    .price-box {
        background-color: #1A1A1A;
        border: 2px solid #00C4B4;
        border-radius: 16px;
        padding: 25px 15px;
        text-align: center;
        margin: 15px 0;
    }
    .price-main {
        font-size: 2.8rem;
        font-weight: bold;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 제목 + 오른쪽 톱니바퀴 ====================
col1, col2 = st.columns([5.5, 1])

with col1:
    st.title("📈 주식 분석")

with col2:
    with st.popover("⚙️", use_container_width=False):
        st.markdown("### 자동 새로고침 설정")
        auto_refresh = st.checkbox("자동 새로고침 사용", value=False)
        refresh_interval = st.slider("새로고침 간격 (초)", 15, 120, 60, step=15)

# 자동 새로고침 실행
if auto_refresh:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=refresh_interval * 1000, key="autorefresh")

# ==================== API Key ====================
FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", os.getenv("FINNHUB_API_KEY", ""))

# ==================== 종목 매핑 ====================
korean_name_map = {
    
}

popular_stocks = {v: k for k, v in korean_name_map.items()}

# ==================== 검색 ====================
search_query = st.text_input("회사명 또는 종목코드 검색", placeholder="삼성전자, 005930, AAPL...")

ticker = "005930.KS"
if search_query:
    matched = [name for name in popular_stocks.keys() if search_query.lower() in name.lower()]
    if matched:
        ticker = popular_stocks[matched[0]]
    else:
        ticker = search_query.strip().upper()
        if ticker.isdigit() and len(ticker) == 6:
            ticker += ".KS"

company_name = korean_name_map.get(ticker, ticker)

# ==================== Finnhub 실시간 가격 함수 ====================
def get_finnhub_price(symbol, api_key):
    if not api_key:
        return None
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if "c" in data and data["c"] > 0:
            return {
                "current": data["c"],
                "high": data["h"],
                "low": data["l"],
                "prev_close": data["pc"],
                "time": datetime.fromtimestamp(data.get("t", 0)).strftime("%H:%M:%S")
            }
    except:
        return None
    return None

# ==================== 분석 ====================
try:
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")
    info = stock.info

    if df.empty:
        st.error("데이터를 불러올 수 없습니다.")
    else:
        current_price = float(df['Close'].iloc[-1])
        daily_change_pct = ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100 if len(df) >= 2 else 0
        is_korean = '.KS' in ticker or '.KQ' in ticker
        usd_to_krw = 1380

        def fmt(price, kr):
            return f"₩{int(price):,}" if kr else f"${price:,.2f}"

        if FINNHUB_API_KEY:
            realtime = get_finnhub_price(ticker, FINNHUB_API_KEY)
            if realtime:
                current_price = realtime["current"]
                daily_change_pct = ((current_price - realtime["prev_close"]) / realtime["prev_close"]) * 100

        # 상단 정보 + 버튼
        col_name, col1, col2 = st.columns([4, 1.3, 1.3])
        with col_name:
            st.subheader(f"{company_name} ({ticker})")
        with col1:
            q = f"{ticker} OR {company_name.split()[0]}" if is_korean else f"${ticker}"
            st.link_button("커뮤니티", f"https://x.com/search?q={q}&src=typed_query&f=live", use_container_width=True)
        with col2:
            if st.button("📊 1일 봉 분석", use_container_width=True):
                st.session_state.show_daily = True

        analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"분석 시점: {analysis_time}")

        # 현재가
        st.markdown(f"""
        <div class="price-box">
            <div style="color:#AAAAAA; font-size:1rem;">현재가</div>
            <div class="price-main">{fmt(current_price, is_korean)}</div>
            <div style="color:#AAAAAA; font-size:1.2rem;">{f"(${current_price / usd_to_krw:.2f})" if is_korean else f"(₩{current_price * usd_to_krw:,.0f})"}</div>
            <div style="font-size:1.6rem; margin-top:8px; color:{'#00C853' if daily_change_pct >= 0 else '#FF5252'}">
                {daily_change_pct:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ==================== 1일 봉 분석 ====================
        if st.session_state.get("show_daily", False):
            st.subheader("📊 1일 봉 차트 분석")
            daily_df = stock.history(period="1y", interval="1d")
            # ... (1일 봉 분석 로직 - 이전에 쓰던 코드 그대로 넣으세요)

        # ==================== 기본 재무 지표 ====================
        st.subheader("📊 기본 재무 지표")
        per = info.get('trailingPE')
        pbr = info.get('priceToBook')
        eps = info.get('trailingEps')
        roe = info.get('returnOnEquity')

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("PER", f"{per:.2f}" if per else "N/A")
        with col2: st.metric("PBR", f"{pbr:.2f}" if pbr else "N/A")
        with col3: st.metric("EPS", f"{eps:.2f}" if eps else "N/A")
        with col4: st.metric("ROE", f"{roe*100:.2f}%" if roe else "N/A")

        # ==================== 기술적 신호 ====================
        st.subheader("📈 기술적 신호")
        # ... (이전 코드 그대로)

        # ==================== 종합 의견 ====================
        st.subheader("📌 종합 의견")
        # ... (이전 코드 그대로)

        # ==================== 추천 가격 ====================
        st.subheader("🎯 추천 가격")
        # ... (이전 코드 그대로)

except Exception as e:
    st.error(f"오류: {str(e)}")

st.caption("📈 주식 분석 | Yahoo Finance + Finnhub | 참고용입니다.")
