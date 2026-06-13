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
korean_name_map = {     # ==================== 코스피 대형주 ====================
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "207940.KS": "삼성바이오로직스",
    "373220.KS": "LG에너지솔루션", "005380.KS": "현대차", "000270.KS": "기아",
    "005490.KS": "POSCO홀딩스", "028260.KS": "삼성물산", "012330.KS": "현대모비스",
    "051910.KS": "LG화학", "006400.KS": "삼성SDI", "035720.KS": "카카오",
    "035420.KS": "네이버", "259960.KS": "크래프톤", "352820.KS": "하이브",

    # ==================== 코스닥 (반도체/소부장) ====================
    "042700.KS": "한미반도체", "058470.KS": "리노공업", "277810.KS": "레인보우로보틱스",
    "030530.KS": "원익IPS", "036930.KS": "주성엔지니어링", "031980.KS": "피에스케이",
    "095610.KS": "테스", "039030.KS": "이오테크닉스", "074600.KS": "원익QnC",
    "357780.KS": "솔브레인", "005290.KS": "동진쎄미켐", "213420.KS": "덕산네오룩스",
    "403870.KS": "HPSP", "036420.KS": "코미코", "032500.KS": "케이엠더블유",
    "071970.KS": "STX", "006260.KS": "LS", "010120.KS": "LS ELECTRIC",
    "089030.KS": "테크윙", "064760.KS": "티에스이", "089850.KS": "유비퀘스트",
    "089790.KS": "제이앤티씨", "064350.KS": "현대로템",

    # ==================== 코스닥 (2차전지/배터리) ====================
    "086520.KS": "에코프로", "247540.KS": "에코프로비엠", "066970.KS": "엘앤에프",
    "003670.KS": "포스코퓨처엠",

    # ==================== 코스닥 (바이오/헬스케어) ====================
    "068270.KS": "셀트리온", "128940.KS": "한미약품", "185750.KS": "종근당",
    "006280.KS": "녹십자", "000100.KS": "유한양행", "096530.KS": "바이오엔텍",

    # ==================== 코스닥 (엔터/게임/콘텐츠) ====================
    "122870.KS": "와이지엔터", "041510.KS": "에스엠", "035900.KS": "JYP Ent.",
    "263750.KS": "펄어비스", "112040.KS": "위메이드", "078340.KS": "컴투스",
    "251270.KS": "넷마블", "293490.KS": "카카오게임즈", "036570.KS": "엔씨소프트",
    "067160.KS": "아프리카TV",

    # ==================== 해외 주식 ====================
    "AAPL": "애플", "MSFT": "마이크로소프트", "GOOGL": "알파벳", "AMZN": "아마존",
    "META": "메타", "NVDA": "엔비디아", "TSLA": "테슬라", "AVGO": "브로드컴",
    "AMD": "AMD", "INTC": "인텔", "QCOM": "퀄컴", "SMCI": "슈퍼마이크로컴퓨터",
    "ARM": "ARM", "TSM": "TSMC", "ASML": "ASML", "MU": "마이크론",
    "KLAC": "KLA", "LRCX": "램리서치", "PLTR": "팔란티어", "CRWD": "크라우드스트라이크",
    "SNOW": "스노우플레이크", "IONQ": "아이온큐", "RGTI": "리게티",
    "DDOG": "데이터독", "NOW": "서비스나우", "ADBE": "어도비",
    "CRM": "세일즈포스", "INTU": "인튜이트", "MSTR": "마이크로스트래티지",
    "NFLX": "넷플릭스", "DIS": "디즈니", "PYPL": "페이팔", "COIN": "코인베이스",
    "EA": "EA", "TTWO": "테이크투인터랙티브", "SPOT": "스포티파이",
    "COST": "코스트코", "LLY": "일라이릴리", "UNH": "유나이티드헬스",
    "JNJ": "존슨앤드존슨", "V": "비자", "MA": "마스터카드",
    "BRK.B": "버크셔해서웨이", "ISRG": "인튜이티브서지컬", "REGN": "리제네론", }  # 이전에 사용하던 큰 딕셔너리 그대로 사용

popular_stocks = {v: k for k, v in korean_name_map.items()}

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

# ==================== 데이터 로드 ====================
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

    # Finnhub 실시간
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

    # ==================== 기본 정보 표시 ====================
    col_name, col_btn = st.columns([5, 1.5])
    with col_name:
        st.subheader(f"{company_name} ({ticker})")
    with col_btn:
        q = f"{ticker} OR {company_name.split()[0]}" if is_korean else f"${ticker}"
        st.link_button("커뮤니티", f"https://x.com/search?q={q}&src=typed_query&f=live", use_container_width=True)

    st.caption(f"{curr_label}{realtime_info}")

    # 현재가 박스
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

    # ==================== 일봉 차트 분석 버튼 ====================
    if st.button("📊 일봉 차트 분석", use_container_width=True):
        with st.spinner("일봉 기준으로 분석 중..."):
            # 일봉 데이터
            daily_df = stock.history(period="1y", interval="1d")

            # 일봉 기술적 지표
            daily_delta = daily_df['Close'].diff()
            daily_gain = (daily_delta.where(daily_delta > 0, 0)).rolling(window=14).mean()
            daily_loss = (-daily_delta.where(daily_delta < 0, 0)).rolling(window=14).mean()
            daily_rs = daily_gain / daily_loss
            daily_rsi = 100 - (100 / (1 + daily_rs))
            daily_rsi_value = float(daily_rsi.iloc[-1])

            daily_ma20 = daily_df['Close'].rolling(20).mean().iloc[-1]
            daily_ma60 = daily_df['Close'].rolling(60).mean().iloc[-1]

            daily_support = float(daily_df['Low'].rolling(20).min().iloc[-1])
            daily_resistance = float(daily_df['High'].rolling(20).max().iloc[-1])

            # 일봉 분석 판단
            if current_price > daily_ma20 and daily_rsi_value < 70:
                daily_judgment = "상승 추세 유지 중"
                daily_reason = "20일 이동평균 위에서 거래되고 있으며, RSI도 과매수 구간이 아닙니다."
            elif current_price < daily_ma20 and daily_rsi_value > 30:
                daily_judgment = "조정 중"
                daily_reason = "20일 이동평균을 하회하고 있으며, 단기 모멘텀이 약합니다."
            elif daily_rsi_value > 70:
                daily_judgment = "단기 과열"
                daily_reason = "RSI가 70을 상회하여 단기 조정 위험이 있습니다."
            elif daily_rsi_value < 30:
                daily_judgment = "단기 과매도"
                daily_reason = "RSI가 30 이하로 단기 반등 가능성이 있습니다."
            else:
                daily_judgment = "중립"
                daily_reason = "뚜렷한 방향성 없이 횡보 중입니다."

            st.subheader("📊 일봉 차트 분석 결과")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("일봉 RSI (14)", f"{daily_rsi_value:.1f}")
                st.metric("20일 이동평균 대비", "상회" if current_price > daily_ma20 else "하회")
            with col2:
                st.metric("일봉 지지선", fmt(daily_support, is_korean))
                st.metric("일봉 저항선", fmt(daily_resistance, is_korean))

            st.markdown(f"""
            **일봉 판단**: {daily_judgment}  
            **이유**: {daily_reason}
            """)

            # 일봉 기반 간단 추천
            if daily_rsi_value < 35 and current_price > daily_ma20:
                st.success("일봉 기준: 단기 반등 기대 가능 구간")
            elif daily_rsi_value > 65:
                st.warning("일봉 기준: 단기 조정 리스크 존재")
            else:
                st.info("일봉 기준: 방향성 관망 구간")

# ==================== 기존 기본 분석 (재무 + 기술 + 종합 의견) ====================
# (이전 코드의 재무 지표, 기술적 신호, 종합 의견 부분 그대로 유지)
