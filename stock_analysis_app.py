import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
import os

st.set_page_config(page_title="주식 분석", layout="wide", page_icon="📈")

# ==================== 스타일 ====================
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
</style>
""", unsafe_allow_html=True)

st.title("📈 주식 분석")

FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", os.getenv("FINNHUB_API_KEY", ""))

# ==================== 종목 매핑 ====================
korean_name_map = {
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "207940.KS": "삼성바이오로직스",
    "373220.KS": "LG에너지솔루션", "005380.KS": "현대차", "000270.KS": "기아",
    "005490.KS": "POSCO홀딩스", "028260.KS": "삼성물산", "012330.KS": "현대모비스",
    "051910.KS": "LG화학", "006400.KS": "삼성SDI", "035720.KS": "카카오",
    "035420.KS": "네이버", "259960.KS": "크래프톤", "352820.KS": "하이브",
    "042700.KS": "한미반도체", "058470.KS": "리노공업", "277810.KS": "레인보우로보틱스",
    "030530.KS": "원익IPS", "036930.KS": "주성엔지니어링", "031980.KS": "피에스케이",
    "095610.KS": "테스", "039030.KS": "이오테크닉스", "074600.KS": "원익QnC",
    "357780.KS": "솔브레인", "005290.KS": "동진쎄미켐", "213420.KS": "덕산네오룩스",
    "403870.KS": "HPSP", "036420.KS": "코미코", "086520.KS": "에코프로",
    "247540.KS": "에코프로비엠", "066970.KS": "엘앤에프", "003670.KS": "포스코퓨처엠",
    "068270.KS": "셀트리온", "128940.KS": "한미약품", "185750.KS": "종근당",
    "006280.KS": "녹십자", "000100.KS": "유한양행", "096530.KS": "바이오엔텍",
    "122870.KS": "와이지엔터", "041510.KS": "에스엠", "035900.KS": "JYP Ent.",
    "263750.KS": "펄어비스", "112040.KS": "위메이드", "078340.KS": "컴투스",
    "251270.KS": "넷마블", "293490.KS": "카카오게임즈", "036570.KS": "엔씨소프트",
    "067160.KS": "아프리카TV",
}

popular_stocks = {v: k for k, v in korean_name_map.items()}

# ==================== 검색 ====================
search_query = st.text_input("회사명 또는 종목코드 검색", placeholder="삼성전자, 005930, AAPL, TSLA...")

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
        daily_change_pct = ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100 if len(df) >= 2 else 0

        is_korean = '.KS' in ticker or '.KQ' in ticker
        usd_to_krw = 1380

        def fmt(price, kr):
            return f"₩{int(price):,}" if kr else f"${price:,.2f}"

        # === 기본 재무 지표 ===
        per = info.get('trailingPE')
        pbr = info.get('priceToBook')
        eps = info.get('trailingEps')
        roe = info.get('returnOnEquity')

        # === RSI 계산 ===
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty else None

        # === 이동평균선 신호 ===
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma_signal = "상승 추세" if current_price > ma20 else "하락 추세"

        # Finnhub 실시간 적용
        realtime_info = ""
        if FINNHUB_API_KEY:
            realtime = get_finnhub_price(ticker, FINNHUB_API_KEY)
            if realtime:
                current_price = realtime["current"]
                daily_change_pct = ((current_price - realtime["prev_close"]) / realtime["prev_close"]) * 100
                realtime_info = f" | 실시간: {realtime['time']}"
                st.success(f"✅ Finnhub 실시간 가격 적용 완료 ({realtime['time']})")

        if is_korean:
            main_price = fmt(current_price, True)
            sub_price = f"(${current_price / usd_to_krw:.2f})"
            curr_label = "🇰🇷 한국 원화 (달러 참고)"
        else:
            main_price = fmt(current_price, False)
            sub_price = f"(₩{current_price * usd_to_krw:,.0f})"
            curr_label = "🇺🇸 달러 (원화 참고)"

        support = float(df['Low'].rolling(20).min().iloc[-1])
        resistance = float(df['High'].rolling(20).max().iloc[-1])
        high_52w = float(df['High'].max())
        low_52w = float(df['Low'].min())

        # 회사명 + 커뮤니티
        col_name, col_btn = st.columns([5, 1.5])
        with col_name:
            st.subheader(f"{company_name} ({ticker})")
        with col_btn:
            q = f"{ticker} OR {company_name.split()[0]}" if is_korean else f"${ticker}"
            st.link_button("커뮤니티", f"https://x.com/search?q={q}&src=typed_query&f=live", use_container_width=True)

        st.caption(f"{curr_label}{realtime_info}")

        # 현재가
        st.markdown(f"""
        <div class="price-box">
            <div style="color:#AAAAAA; font-size:1rem;">현재가</div>
            <div class="price-main">{main_price}</div>
            <div style="color:#AAAAAA; font-size:1.2rem;">{sub_price}</div>
            <div style="font-size:1.6rem; margin-top:8px; color:{'#00C853' if daily_change_pct >= 0 else '#FF5252'}">
                {daily_change_pct:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ==================== 기본 재무 지표 ====================
        st.subheader("📊 기본 재무 지표")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("PER", f"{per:.2f}" if per else "N/A")
        with col2: st.metric("PBR", f"{pbr:.2f}" if pbr else "N/A")
        with col3: st.metric("EPS", f"{eps:.2f}" if eps else "N/A")
        with col4: st.metric("ROE", f"{roe*100:.2f}%" if roe else "N/A")

        # ==================== 기술적 신호 ====================
        st.subheader("📈 기술적 신호")
        col1, col2 = st.columns(2)
        with col1:
            if current_rsi:
                rsi_status = "과매수" if current_rsi > 70 else "과매도" if current_rsi < 30 else "중립"
                st.metric("RSI (14일)", f"{current_rsi:.1f} ({rsi_status})")
        with col2:
            st.metric("20일 이동평균 대비", ma_signal)

        # 지지/저항/52주
        col1, col2 = st.columns(2)
        with col1: st.metric("지지선 (20일)", fmt(support, is_korean))
        with col2: st.metric("저항선 (20일)", fmt(resistance, is_korean))

        col3, col4 = st.columns(2)
        with col3: st.metric("52주 최고가", fmt(high_52w, is_korean))
        with col4: st.metric("52주 최저가", fmt(low_52w, is_korean))

        # ==================== 종합 의견 (구조화) ====================
        st.subheader("📌 종합 의견")

        # 간단한 판단 로직
        if current_price <= support * 1.02 and daily_change_pct > -3:
            judgment = "🟢 구매 적극 추천"
            strength = "지지선 근처에서 가격이 안정적이며, 최근 하락폭이 크지 않습니다."
            weakness = "단기 반등이 나오더라도 강한 상승 모멘텀은 아직 확인되지 않았습니다."
            risk = "추가 하락 시 지지선 이탈 가능성이 존재합니다."
        elif current_price >= resistance * 0.98 and daily_change_pct > 5:
            judgment = "🟡 전망 관망"
            strength = "상승 추세가 이어지고 있으며 단기 모멘텀이 양호합니다."
            weakness = "저항선에 근접해 단기 조정 위험이 있습니다."
            risk = "단기 차익실현 매물이 나올 가능성이 있습니다."
        elif daily_change_pct < -8:
            judgment = "🔴 단기 손절 고려"
            strength = "가격 조정이 깊게 진행되었습니다."
            weakness = "단기 모멘텀이 약하고 추가 하락 위험이 있습니다."
            risk = "지지가 약해 추가 급락 가능성이 있습니다."
        else:
            judgment = "🔵 홀딩 추천"
            strength = "특별한 과열이나 과매도 신호가 보이지 않습니다."
            weakness = "강한 상승 모멘텀도, 뚜렷한 하락 신호도 없는 중립 구간입니다."
            risk = "방향성이 명확하지 않아 단기 변동성이 지속될 수 있습니다."

        color = "#00C853" if "구매" in judgment else "#FF5252" if "손절" in judgment else "#FFD700" if "관망" in judgment else "#00B0FF"

        st.markdown(f"""
        <div style="background-color:{color}15; border:2px solid {color}; 
                    padding:16px; border-radius:12px; text-align:center; font-size:1.3rem; font-weight:bold; color:{color};">
            {judgment}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        **강점**: {strength}  
        **약점**: {weakness}  
        **리스크**: {risk}
        """)

        # 추천 가격
        st.subheader("🎯 추천 가격")
        r1, r2, r3 = st.columns(3)
        with r1: st.success(f"**진입 추천가**\n{fmt(current_price * 0.98, is_korean)}")
        with r2: st.success(f"**목표가**\n{fmt(current_price * 1.05, is_korean)}")
        with r3: st.error(f"**손절 추천가**\n{fmt(current_price * 0.95, is_korean)}")

except Exception as e:
    st.error(f"오류: {str(e)}")

st.caption("📈 주식 분석 | Yahoo Finance + Finnhub | 참고용입니다.")
