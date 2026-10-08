"""
주식 시황 페이지 (메인 화면)
미국/한국 주요 지수, 환율·금리·변동성·원자재 지표, 가상자산 시세를 한눈에 봅니다.
"""

from datetime import date

import streamlit as st
from utils import fetch_market_snapshot

st.set_page_config(page_title="주식 시황", layout="wide")

st.title("주식 시황")
st.caption("주요 지수/지표/가상자산 현황입니다. 카드를 클릭하면 새 창에서 상세 시세/차트를 볼 수 있습니다. 카드 아래 작은 글씨는 최근 1년(52주) 최고 종가 대비 현재 위치입니다.")

# 지표 하나당 한 줄: (섹션, 라벨, 티커, 값 포맷 함수, 상세 시세 링크)
# 링크는 네이버금융(신버전 stock.naver.com)이 지원하는 지표는 네이버로, 네이버가 다루지 않는
# 해외지수/원자재/금리/가상자산은 investing.com·업비트로 연결합니다.
US_FMT = lambda v: f"{v:,.2f}"
INDICATORS = {
    "미국": [
        ("S&P 500", "^GSPC", US_FMT, "https://www.investing.com/indices/us-spx-500"),
        ("나스닥 종합", "^IXIC", US_FMT, "https://www.investing.com/indices/nasdaq-composite"),
        ("다우존스", "^DJI", US_FMT, "https://www.investing.com/indices/us-30"),
        ("필라델피아 반도체", "^SOX", US_FMT, "https://www.investing.com/indices/phlx-semiconductor"),
        ("나스닥 100", "^NDX", US_FMT, "https://www.investing.com/indices/nq-100"),
    ],
    "한국": [
        ("코스피", "^KS11", US_FMT, "https://stock.naver.com/domestic/index/KOSPI/price"),
        ("코스닥", "^KQ11", US_FMT, "https://stock.naver.com/domestic/index/KOSDAQ/price"),
        # 코스피200 지수(^KS200)는 야후에 당일 1건만 있어 변동률/52주 계산이 불가 -> 추종 ETF(KODEX 200) 가격으로 대신 표시
        ("코스피200 (KODEX 200)", "229200.KS", US_FMT, "https://stock.naver.com/domestic/index/KPI200/price"),
    ],
    "환율 · 금리 · 변동성": [
        ("원/달러 환율", "KRW=X", US_FMT, "https://stock.naver.com/marketindex/exchange/FX_USDKRW/price"),
        ("원/100엔 환율", "JPYKRW=X", lambda v: f"{v * 100:,.2f}", "https://stock.naver.com/marketindex/exchange/FX_JPYKRW/price"),
        ("미국 국채 10년 금리(%)", "^TNX", lambda v: f"{v:,.3f}", "https://www.investing.com/rates-bonds/u.s.-10-year-bond-yield"),
        ("미국 국채 30년 금리(%)", "^TYX", lambda v: f"{v:,.3f}", "https://www.investing.com/rates-bonds/u.s.-30-year-bond-yield"),
        ("달러 인덱스", "DX-Y.NYB", US_FMT, "https://www.investing.com/currencies/us-dollar-index"),
        ("VIX (공포지수)", "^VIX", US_FMT, "https://www.investing.com/indices/volatility-s-p-500"),
    ],
    "에너지 · 금속": [
        ("WTI 유가", "CL=F", US_FMT, "https://www.investing.com/commodities/crude-oil"),
        ("국제 금", "GC=F", lambda v: f"{v:,.1f}", "https://stock.naver.com/marketindex/metals/M04020000/price"),
        ("국제 은", "SI=F", US_FMT, "https://www.investing.com/commodities/silver"),
        ("구리", "HG=F", lambda v: f"{v:,.3f}", "https://www.investing.com/commodities/copper"),
    ],
}
CRYPTO = [
    ("비트코인", "BTC-USD", "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC"),
    ("이더리움", "ETH-USD", "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-ETH"),
    ("리플", "XRP-USD", "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-XRP"),
    ("솔라나", "SOL-USD", "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-SOL"),
]

all_tickers = [t for items in INDICATORS.values() for _, t, _, _ in items] + [t for _, t, _ in CRYPTO]

with st.spinner("시세 불러오는 중..."):
    snapshot, fetched_at = fetch_market_snapshot(all_tickers)

head_left, head_right = st.columns([5, 1])
head_left.caption(f"마지막 갱신: {fetched_at:%Y-%m-%d %H:%M:%S} (5분간 캐시됨)")
if head_right.button("새로고침"):
    fetch_market_snapshot.clear()
    st.rerun()


def render_metric_card(col, label, value_text, delta_text, pct_from_high, url):
    """st.metric과 비슷하게 생겼지만, 클릭하면 새 창으로 해당 지표의 상세 시세 사이트가 열리는 카드.
    맨 아래 줄에 52주 고점 대비 위치를 작게 표시."""
    if delta_text and delta_text.startswith("+"):
        delta_color = "#09ab3b"
    elif delta_text and delta_text.startswith("-"):
        delta_color = "#ff2b2b"
    else:
        delta_color = "#888"
    delta_html = f'<div style="font-size:0.85rem;color:{delta_color};margin-top:2px;">{delta_text}</div>' if delta_text else ""
    high_html = (
        f'<div style="font-size:0.72rem;color:#999;margin-top:4px;">52주 고점 대비 {pct_from_high:+.1f}%</div>'
        if pct_from_high is not None else ""
    )
    # 줄 앞에 들여쓰기가 들어가면 마크다운이 코드 블록으로 오해해 HTML이 그대로 노출되므로 한 줄로 이어붙임
    html = (
        f'<a href="{url}" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;">'
        '<div style="border:1px solid rgba(128,128,128,0.25);border-radius:8px;padding:10px 14px;margin-bottom:8px;">'
        f'<div style="font-size:0.8rem;color:#888;">{label}</div>'
        f'<div style="font-size:1.5rem;font-weight:600;">{value_text}</div>'
        f"{delta_html}{high_html}"
        "</div></a>"
    )
    col.markdown(html, unsafe_allow_html=True)


def section_date_caption(tickers):
    """섹션에 포함된 지표들의 데이터 기준일(가장 최근 날짜)을 '기준: 2026-10-07 종가' 형태로 표시"""
    dates = [snapshot[t]["date"] for t in tickers if t in snapshot]
    if dates:
        latest = max(dates)
        suffix = " (당일)" if latest == date.today() else " 종가"
        st.caption(f"기준: {latest:%Y-%m-%d}{suffix}")


def show_row(items):
    """items: [(라벨, 티커, 값 포맷 함수, 링크), ...] 를 한 줄에 나란히 카드로 표시"""
    cols = st.columns(len(items))
    for col, (label, ticker, fmt, url) in zip(cols, items):
        info = snapshot.get(ticker)
        if info is None:
            col.metric(label, "조회 실패")
            continue
        delta = f"{info['change']:+.2f}%" if info["change"] is not None else None
        render_metric_card(col, label, fmt(info["price"]), delta, info["pct_from_high"], url)


def show_section(section):
    items = INDICATORS[section]
    section_date_caption([t for _, t, _, _ in items])
    show_row(items)


st.subheader("미국")
show_section("미국")

st.divider()
st.subheader("한국")
show_section("한국")

st.divider()
st.subheader("지표")
st.caption("환율 · 금리 · 변동성")
show_section("환율 · 금리 · 변동성")
st.write("")
st.caption("에너지 · 금속")
show_section("에너지 · 금속")

st.divider()
st.subheader("가상자산")
st.caption("원화 환산 가격입니다 (국내 거래소 가격과는 프리미엄 차이로 약간 다를 수 있습니다).")

rate = snapshot.get("KRW=X", {}).get("price")

cols = st.columns(len(CRYPTO))
for col, (label, ticker, url) in zip(cols, CRYPTO):
    info = snapshot.get(ticker)
    if info is None:
        col.metric(label, "조회 실패")
        continue
    krw_price = info["price"] * rate if rate is not None else None
    value_text = f"{krw_price:,.0f} 원" if krw_price is not None else f"${info['price']:,.2f}"
    delta = f"{info['change']:+.2f}%" if info["change"] is not None else None
    render_metric_card(col, label, value_text, delta, info["pct_from_high"], url)
