"""
한국주식 대시보드
회사명(예: 삼성전자) 또는 종목코드로 검색해서 차트/지표/뉴스를 봅니다.
"""

import streamlit as st

st.set_page_config(layout="wide")
import pandas as pd
import yfinance as yf
from utils import KR_TICKERS, resolve_kr_ticker, calculate_rsi, translate_to_korean

PERIOD_TRADING_DAYS = {"5d": 5, "1mo": 21, "3mo": 63, "6mo": 126, "1y": 252, "5y": None}


def get_display_price(info):
    """개별종목은 currentPrice, ETF는 regularMarketPrice에 가격이 들어있어서 순서대로 확인하는 함수"""
    return info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")


def get_price_history_with_ma(stock_obj):
    """이동평균(20/60/120일)을 정확히 계산하기 위해 항상 5년치를 받아온 뒤, 필요한 지표를 계산해서 돌려주는 함수"""
    data = stock_obj.history(period="5y")
    if data.empty:
        return None
    data = data[data["Close"].notna()]  # 오늘 장 데이터가 아직 안 채워진 빈(NaN) 행 제거
    close = data["Close"]
    df = pd.DataFrame({"Close": close})
    df["MA20"] = close.rolling(window=20).mean()
    df["MA60"] = close.rolling(window=60).mean()
    df["MA120"] = close.rolling(window=120).mean()
    df["Volume"] = data["Volume"]
    return df


def get_key_stats(info, rsi_value):
    """yfinance info 딕셔너리에서 주요 지표만 뽑아내는 함수"""
    return {
        "현재가": get_display_price(info),
        "시가총액": info.get("marketCap") or info.get("totalAssets"),  # ETF는 marketCap 대신 totalAssets(순자산총액)
        "PER (주가수익비율)": info.get("trailingPE"),
        "52주 최고가": info.get("fiftyTwoWeekHigh"),
        "52주 최저가": info.get("fiftyTwoWeekLow"),
        "배당수익률": info.get("dividendYield") or info.get("yield"),
        "거래량": info.get("volume") or info.get("regularMarketVolume"),
        "RSI(14) - 과열/인기도": rsi_value,
    }


def get_news(ticker_obj, limit=8):
    """관련 뉴스 리스트를 받아오는 함수"""
    try:
        return ticker_obj.get_news(count=limit)
    except Exception:
        return []


st.title("한국주식 대시보드")
st.caption("일반 종목뿐 아니라 KODEX/TIGER 같은 ETF도 조회 가능합니다 (목록에 미리 등록되어 있거나, 종목코드를 직접 입력하면 됩니다).")

search_mode = st.radio("검색 방법", ["목록에서 회사/ETF 선택", "회사명/종목코드 직접 입력"], horizontal=True)

if search_mode == "목록에서 회사/ETF 선택":
    company = st.selectbox("회사 또는 ETF 선택", sorted(KR_TICKERS.keys()))
    user_input = company
else:
    user_input = st.text_input("회사명/ETF명 또는 종목코드 입력 (예: 삼성전자, KODEX 200, 005930, 005930.KS)", value="삼성전자")

period = st.selectbox("차트 기간", ["5d", "1mo", "3mo", "6mo", "1y", "5y"], index=3)

if user_input:
    ticker_symbol = resolve_kr_ticker(user_input)

    if ticker_symbol is None:
        st.error(f"'{user_input}'를 목록에서 찾을 수 없습니다. 종목코드(6자리 숫자) 또는 '005930.KS' 형태로 입력해주세요.")
    else:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info

        # 코스피(.KS)로 시도했는데 없으면 코스닥(.KQ)로 재시도
        if (not info or get_display_price(info) is None) and ticker_symbol.endswith(".KS"):
            alt_symbol = ticker_symbol.replace(".KS", ".KQ")
            alt_stock = yf.Ticker(alt_symbol)
            alt_info = alt_stock.info
            if alt_info and get_display_price(alt_info) is not None:
                ticker_symbol, stock, info = alt_symbol, alt_stock, alt_info

        if not info or get_display_price(info) is None:
            st.error(f"'{ticker_symbol}' 정보를 찾을 수 없습니다.")
        else:
            st.subheader(f"{info.get('longName', ticker_symbol)} ({ticker_symbol})")

            full_df = get_price_history_with_ma(stock)
            rsi_series = calculate_rsi(full_df["Close"]) if full_df is not None else pd.Series(dtype=float)
            rsi_value = rsi_series.iloc[-1] if not rsi_series.empty else None

            # --- 주요 지표 ---
            stats = get_key_stats(info, rsi_value)
            cols = st.columns(4)
            items = list(stats.items())
            money_labels = {"현재가", "시가총액", "52주 최고가", "52주 최저가"}  # 원화 금액은 소수점 없이 표시
            for i, (label, value) in enumerate(items):
                with cols[i % 4]:
                    if value is None or (isinstance(value, float) and pd.isna(value)):
                        st.metric(label, "N/A")
                    elif "수익률" in label:
                        st.metric(label, f"{value:.2f}%")
                    elif label == "거래량":
                        st.metric(label, f"{value:,.0f}")
                    elif "RSI" in label:
                        hint = "과열(인기 많음)" if value >= 70 else ("과매도" if value <= 30 else "보통")
                        st.metric(label, f"{value:.1f} ({hint})")
                    elif label in money_labels:
                        st.metric(label, f"{value:,.0f}")
                    else:
                        st.metric(label, f"{value:,.2f}" if isinstance(value, float) else value)

            # --- 차트 ---
            st.subheader("가격 차트 + 이동평균선")
            ma_col1, ma_col2, ma_col3 = st.columns(3)
            show_ma20 = ma_col1.checkbox("20일", value=True, key="kr_ma20")
            show_ma60 = ma_col2.checkbox("60일", value=False, key="kr_ma60")
            show_ma120 = ma_col3.checkbox("120일", value=False, key="kr_ma120")

            display_days = PERIOD_TRADING_DAYS[period]
            columns_to_show = ["Close"]
            if show_ma20:
                columns_to_show.append("MA20")
            if show_ma60:
                columns_to_show.append("MA60")
            if show_ma120:
                columns_to_show.append("MA120")

            chart_data = full_df[columns_to_show]
            if display_days is not None:
                chart_data = chart_data.tail(display_days)
            st.line_chart(chart_data)

            # --- 뉴스 ---
            st.subheader("관련 뉴스")

            code_only = ticker_symbol.replace(".KS", "").replace(".KQ", "")
            naver_url = f"https://finance.naver.com/item/news_news.naver?code={code_only}"
            stockplus_url = f"https://www.stockplus.com/m/stocks/KOREA-A{code_only}"

            link_col1, link_col2, _ = st.columns([1, 1, 3])
            link_col1.link_button("네이버 금융에서 한국어 뉴스 보기 ↗", naver_url)
            link_col2.link_button("증권플러스에서 보기 ↗", stockplus_url)
            st.markdown("**아래는 야후파이낸스 뉴스(영어권 기사 위주)입니다. 한국어 기사는 위 버튼들로 확인하세요.**")

            news_items = get_news(stock)
            if not news_items:
                st.write("뉴스를 불러올 수 없습니다.")
            else:
                for item in news_items:
                    content = item.get("content", item)
                    title = content.get("title", "제목 없음")
                    link = content.get("canonicalUrl", {}).get("url") or content.get("link", "#")
                    publisher = content.get("provider", {}).get("displayName", "")
                    translated = translate_to_korean(title)
                    st.markdown(f"**[{title}]({link})**")
                    if translated:
                        st.markdown(f"↳ {translated}")
                    st.caption(publisher)
                    st.write("")
