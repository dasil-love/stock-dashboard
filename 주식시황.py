"""
주식 시황 페이지 (메인 화면)
미국/한국 주요 지수, 환율·금리·원자재 지표, 가상자산 시세를 한눈에 봅니다.
"""

import streamlit as st
from utils import get_price_with_day_change, get_usdkrw_rate

st.set_page_config(page_title="주식 시황", layout="wide")

st.title("주식 시황")
st.caption("주요 지수/지표/가상자산 현황입니다. 자동으로 최신 정보를 불러옵니다.")


def show_row(items):
    """items: [(라벨, 티커, 값 포맷 함수), ...] 형태의 리스트를 받아 한 줄에 나란히 표시하는 함수"""
    cols = st.columns(len(items))
    for col, (label, ticker, fmt) in zip(cols, items):
        price, change = get_price_with_day_change(ticker)
        if price is None:
            col.metric(label, "조회 실패")
            continue
        delta = f"{change:+.2f}%" if change is not None else None
        col.metric(label, fmt(price), delta)


st.subheader("미국")
show_row([
    ("S&P 500", "^GSPC", lambda v: f"{v:,.2f}"),
    ("나스닥 종합", "^IXIC", lambda v: f"{v:,.2f}"),
    ("다우존스", "^DJI", lambda v: f"{v:,.2f}"),
    ("필라델피아 반도체", "^SOX", lambda v: f"{v:,.2f}"),
    ("나스닥 100", "^NDX", lambda v: f"{v:,.2f}"),
])

st.subheader("한국")
show_row([
    ("코스피", "^KS11", lambda v: f"{v:,.2f}"),
    ("코스닥", "^KQ11", lambda v: f"{v:,.2f}"),
    ("코스피 200", "^KS200", lambda v: f"{v:,.2f}"),
])

st.subheader("지표")
show_row([
    ("원/달러 환율", "KRW=X", lambda v: f"{v:,.2f}"),
    ("원/유로 환율", "EURKRW=X", lambda v: f"{v:,.2f}"),
    ("WTI 유가", "CL=F", lambda v: f"{v:,.2f}"),
    ("국제 금", "GC=F", lambda v: f"{v:,.1f}"),
])
show_row([
    ("미국 국채 10년 금리(%)", "^TNX", lambda v: f"{v:,.3f}"),
    ("미국 국채 30년 금리(%)", "^TYX", lambda v: f"{v:,.3f}"),
    ("달러 인덱스", "DX-Y.NYB", lambda v: f"{v:,.2f}"),
])

st.subheader("가상자산")
st.caption("원화 환산 가격입니다 (국내 거래소 가격과는 프리미엄 차이로 약간 다를 수 있습니다).")

rate = get_usdkrw_rate()


def show_crypto_row(items):
    cols = st.columns(len(items))
    for col, (label, ticker) in zip(cols, items):
        price, change = get_price_with_day_change(ticker)
        if price is None:
            col.metric(label, "조회 실패")
            continue
        krw_price = price * rate if rate is not None else None
        value_text = f"{krw_price:,.0f} 원" if krw_price is not None else f"${price:,.2f}"
        delta = f"{change:+.2f}%" if change is not None else None
        col.metric(label, value_text, delta)


show_crypto_row([
    ("비트코인", "BTC-USD"),
    ("이더리움", "ETH-USD"),
    ("리플", "XRP-USD"),
    ("솔라나", "SOL-USD"),
])
