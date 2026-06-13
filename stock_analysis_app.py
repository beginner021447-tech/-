import streamlit as st
import yfinance as yf
import requests
import webbrowser
from datetime import datetime

st.set_page_config(page_title="주식 분석", layout="wide", page_icon="📈")

# ==================== 모바일 최적화 스타일 ====================
st.markdown("""
<style>
    .main { background-color: #0F0F0F; color: #EDEDED; }
    .stApp { background-color: #0F0F0F; }
    
    h1 { color: #00C4B4; font-weight: bold; font-size: 1.8rem; }
    h2, h3 { color: #00C4B4; }
    
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
    
    /* 모바일 최적화 */
    @media (max-width: 768px) {
        .price-main {
            font-size: 2.4rem;
        }
        h1 { font-size: 1.6rem; }
        .stMetric {
            font-size: 0.9rem;
        }
        .stButton>button {
            font-size: 0.95rem;
            padding: 0.5rem 1rem;
        }
    }
    
    .stButton>button {
        background-color: #00C4B4;
        color: white;
        border-radius: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 주식 분석")

# ==================== 검색 ====================
search_query = st.text_input(
    "회사명 또는 종목코드 검색",
    placeholder="삼성전자, 005930.KS, AAPL, TSLA..."
)

# ==================== 한국어 이름 매핑 ====================
korean_name_map = {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    "207940.KS": "삼성바이오로직스",
    "373220.KS": "LG에너지솔루션",
    "005380.KS": "현대차",
    "000270.KS": "기아",
    "005490.KS": "POSCO홀딩스",
    "028260.KS": "삼성물산",
    "012330.KS": "현대모비스",
    "051910.KS": "LG화학",
    "006400.KS": "삼성SDI",
    "035720.KS": "카카오",
    "035420.KS": "네이버",
    "259960.KS": "크래프톤",
    "352820.KS": "하이브",
}

popular_stocks = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "삼성바이오로직스": "207940.KS",
    "LG에너지솔루션": "373220.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "POSCO홀딩스": "005490.KS",
    "삼성물산": "028260.KS",
    "현대모비스": "012330.KS",
    "LG화학": "051910.KS",
    "삼성SDI": "006400.KS",
    "카카오": "035720.KS",
    "네이버": "035420.KS",
    "크래프톤": "259960.KS",
    "하이브": "352820.KS",
    "애플": "AAPL",
    "테슬라": "TSLA",
    "엔비디아": "NVDA",
    "마이크로소프트": "MSFT",
    "아마존": "AMZN",
    "구글": "GOOGL",
    "메타": "META",
}

ticker = "005930.KS"
if search_query:
    matched = [name for name in popular_stocks.keys() if search_query.lower() in name.lower()]
    if matched:
        selected = st.selectbox("검색 결과", matched)
        ticker = popular_stocks[selected]
    else:
        ticker = search_query.strip().upper()

# ==================== Finnhub 실시간 가격 ====================
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
        prev_close = float(df['Close'].iloc[0]) if len(df) > 1 else current_price
        change_pct = ((current_price - prev_close) / prev_close) * 100

        company_name = korean_name_map.get(ticker, info.get('longName') or info.get('shortName') or ticker)
        is_korean = '.KS' in ticker
        usd_to_krw = 1380

        def fmt(price, kr):
            return f"₩{int(price):,}" if kr else f"${price:,.2f}"

        # Finnhub 실시간
        realtime_info = ""
        if FINNHUB_API_KEY:
            realtime = get_finnhub_price(ticker, FINNHUB_API_KEY)
            if realtime:
                current_price = realtime["current"]
                change_pct = ((current_price - realtime["prev_close"]) / realtime["prev_close"]) * 100
                realtime_info = f" | 실시간: {realtime['time']}"
                st.success(f"Finnhub 실시간 가격 적용 완료 ({realtime['time']})")

        if is_korean:
            main_price = fmt(current_price, True)
            sub_price = f"(${current_price / usd_to_krw:.2f})"
            curr_label = "🇰🇷 한국 원화 (달러)"
        else:
            main_price = fmt(current_price, False)
            sub_price = f"(₩{current_price * usd_to_krw:,.0f})"
            curr_label = "🇺🇸 달러 (원화)"

        support = float(df['Low'].rolling(20).min().iloc[-1])
        resistance = float(df['High'].rolling(20).max().iloc[-1])
        high_52w = float(df['High'].max())
        low_52w = float(df['Low'].min())

        # 회사명 + 커뮤니티
        col_name, col_btn = st.columns([5, 1.5])
        with col_name:
            st.subheader(f"{company_name} ({ticker})")
        with col_btn:
            if st.button("커뮤니티", use_container_width=True):
                q = f"{ticker} OR {company_name.split()[0]}" if is_korean else f"${ticker}"
                webbrowser.open_new_tab(f"https://x.com/search?q={q}&src=typed_query&f=live")

        st.caption(f"{curr_label}{realtime_info}")

        # 현재가
        st.markdown(f"""
        <div class="price-box">
            <div style="color:#AAAAAA; font-size:1rem;">현재가</div>
            <div class="price-main">{main_price}</div>
            <div style="color:#AAAAAA; font-size:1.2rem;">{sub_price}</div>
            <div style="font-size:1.6rem; margin-top:8px; color:{'#00C853' if change_pct >= 0 else '#FF5252'}">
                {change_pct:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 지표 (모바일에서 2열로 변경)
        col1, col2 = st.columns(2)
        with col1: st.metric("지지선", fmt(support, is_korean))
        with col2: st.metric("저항선", fmt(resistance, is_korean))

        col3, col4 = st.columns(2)
        with col3: st.metric("52주 최고가", fmt(high_52w, is_korean))
        with col4: st.metric("52주 최저가", fmt(low_52w, is_korean))

        # 종합 의견
        st.subheader("📌 종합 의견")

        if current_price <= support * 1.02 and change_pct > -5:
            rec = "🟢 구매 적극 추천"
            reason = "지지선 근처이며 최근 하락폭이 크지 않습니다."
        elif current_price >= resistance * 0.98 and change_pct > 10:
            rec = "🟡 전망 관망"
            reason = "저항선 근처까지 상승했습니다."
        elif change_pct < -15:
            rec = "🔴 손절 고려"
            reason = "1년 기준 큰 하락이 있었습니다."
        else:
            rec = "🔵 홀딩 추천"
            reason = "특별한 과열·과매도 신호가 없습니다."

        color = "#00C853" if "구매" in rec else "#FF5252" if "손절" in rec else "#FFD700" if "관망" in rec else "#00B0FF"

        st.markdown(f"""
        <div style="background-color:{color}15; border:2px solid {color}; 
                    padding:16px; border-radius:12px; text-align:center; font-size:1.3rem; font-weight:bold; color:{color};">
            {rec}
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"**이유**: {reason}")

        # 추천 가격
        st.subheader("🎯 추천 가격")
        r1, r2, r3 = st.columns(3)
        with r1: st.success(f"**진입 추천가**\n{fmt(current_price * 0.98, is_korean)}")
        with r2: st.success(f"**목표가**\n{fmt(current_price * 1.05, is_korean)}")
        with r3: st.error(f"**손절 추천가**\n{fmt(current_price * 0.95, is_korean)}")

except Exception as e:
    st.error(f"오류: {str(e)}")

st.caption("📈 주식 분석 | Yahoo Finance + Finnhub | 참고용입니다.")