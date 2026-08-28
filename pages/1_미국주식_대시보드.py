"""
미국 주식 로컬 대시보드
Streamlit으로 만든 웹 화면에서 종목을 검색하고 차트/지표/뉴스를 봅니다.
"""

import streamlit as st
import pandas as pd
import yfinance as yf
from utils import calculate_rsi, get_naver_worldstock_url, translate_to_korean

st.set_page_config(page_title="주식 대시보드", layout="wide")

PERIOD_TRADING_DAYS = {"5d": 5, "1mo": 21, "3mo": 63, "6mo": 126, "1y": 252, "5y": None}


def get_price_history_with_ma(ticker):
    """이동평균(20/60/120일)을 정확히 계산하기 위해 항상 5년치를 받아온 뒤, 필요한 지표를 계산해서 돌려주는 함수"""
    data = yf.download(ticker, period="5y", interval="1d")
    if data.empty:
        return None
    data = data[data["Close"].notna().squeeze()]  # 오늘 장 데이터가 아직 안 채워진 빈(NaN) 행 제거
    close = data["Close"].squeeze()
    df = pd.DataFrame({"Close": close})
    df["MA20"] = close.rolling(window=20).mean()
    df["MA60"] = close.rolling(window=60).mean()
    df["MA120"] = close.rolling(window=120).mean()
    df["Volume"] = data["Volume"].squeeze()
    return df


def get_key_stats(info, rsi_value, current_price):
    return {
        "현재가": current_price,
        "거래량": info.get("volume") or info.get("regularMarketVolume"),
        "평균거래량": info.get("averageVolume"),
        "PER (주가수익비율)": info.get("trailingPE"),
        "52주 최고가": info.get("fiftyTwoWeekHigh"),
        "52주 최저가": info.get("fiftyTwoWeekLow"),
        "RSI(14) - 과열/인기도": rsi_value,
    }


def get_news(ticker_obj, limit=8):
    try:
        return ticker_obj.get_news(count=limit)
    except Exception:
        return []


st.title("미국 주식 대시보드")

raw_ticker = st.text_input("종목 티커를 입력하세요 (예: AAPL, TSLA, MSFT)", value="AAPL")
ticker = raw_ticker.strip().upper()  # 소문자로 입력해도(aapl 등) 인식되도록 대문자로 통일
period = st.selectbox("차트 기간", ["5d", "1mo", "3mo", "6mo", "1y", "5y"], index=3)

if ticker:
    stock = yf.Ticker(ticker)

    full_df = None
    fetch_error = None
    try:
        full_df = get_price_history_with_ma(ticker)
    except Exception as e:
        fetch_error = e

    # 회사명/PER/52주 최고-최저 같은 부가 정보(.info)는 야후에서 종종 막히므로,
    # 실패해도 무시하고 진행 (테마종목 페이지와 동일한 방식 - 가격 이력만 있으면 화면은 정상 표시)
    info = {}
    if fetch_error is None:
        try:
            info = stock.info
        except Exception:
            info = {}

    if fetch_error is not None:
        st.error("야후 파이낸스에서 가격 데이터를 가져오는 중 오류가 발생했습니다. 아래 오류 내용을 캡처해서 알려주시면 원인을 확인할 수 있습니다.")
        st.exception(fetch_error)
    elif full_df is None:
        st.error(f"'{ticker}' 데이터를 찾을 수 없습니다. 티커를 확인해주세요. (야후 파이낸스 접속이 일시적으로 제한된 경우일 수도 있습니다. 잠시 후 다시 시도해주세요.)")
    else:
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or full_df["Close"].iloc[-1]
        st.subheader(f"{info.get('longName', ticker)} ({ticker})")

        # --- 주요 지표 ---
        rsi_series = calculate_rsi(full_df["Close"])
        rsi_value = rsi_series.iloc[-1] if not rsi_series.empty else None
        stats = get_key_stats(info, rsi_value, current_price)

        cols = st.columns(4)
        money_labels = {"현재가", "52주 최고가", "52주 최저가"}
        for i, (label, value) in enumerate(stats.items()):
            with cols[i % 4]:
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    st.metric(label, "N/A")
                elif label in money_labels:
                    st.metric(label, f"${value:,.2f}")
                elif label in ("거래량", "평균거래량"):
                    st.metric(label, f"{value:,.0f}")
                elif "RSI" in label:
                    hint = "과열(인기 많음)" if value >= 70 else ("과매도" if value <= 30 else "보통")
                    st.metric(label, f"{value:.1f} ({hint})")
                else:
                    st.metric(label, f"{value:.2f}")

        # --- 차트 ---
        st.subheader(f"{ticker} 종가 + 이동평균선")
        ma_col1, ma_col2, ma_col3 = st.columns(3)
        show_ma20 = ma_col1.checkbox("20일", value=True, key="us_ma20")
        show_ma60 = ma_col2.checkbox("60일", value=False, key="us_ma60")
        show_ma120 = ma_col3.checkbox("120일", value=False, key="us_ma120")

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

        exchange = info.get("exchange", "")
        naver_url = get_naver_worldstock_url(ticker, exchange)
        stockplus_url = f"https://www.stockplus.com/m/stocks/USA-{ticker}"

        link_col1, link_col2, _ = st.columns([1, 1, 3])
        link_col1.link_button("네이버 금융에서 보기 ↗", naver_url)
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

        st.subheader("최근 데이터")
        st.dataframe(full_df.tail(10))
