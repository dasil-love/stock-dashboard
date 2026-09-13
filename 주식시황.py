"""
주식 시황 페이지 (메인 화면)
미국/한국 주요 지수, 환율·금리·원자재 지표, 가상자산 시세를 한눈에 봅니다.
"""

import streamlit as st
from utils import get_price_with_day_change, get_usdkrw_rate

st.set_page_config(page_title="주식 시황", layout="wide")

st.title("주식 시황")
st.caption("주요 지수/지표/가상자산 현황입니다. 자동으로 최신 정보를 불러옵니다. 카드를 클릭하면 새 창에서 상세 시세/차트를 볼 수 있습니다.")

# 지표별 상세 시세 사이트 링크. 네이버금융(신버전 stock.naver.com)이 지원하는 지표는 네이버로,
# 네이버가 다루지 않는 해외지수/원자재/금리/가상자산은 investing.com·업비트로 연결합니다.
INDICATOR_LINKS = {
    "^GSPC": "https://www.investing.com/indices/us-spx-500",
    "^IXIC": "https://www.investing.com/indices/nasdaq-composite",
    "^DJI": "https://www.investing.com/indices/us-30",
    "^SOX": "https://www.investing.com/indices/phlx-semiconductor",
    "^NDX": "https://www.investing.com/indices/nq-100",
    "^KS11": "https://stock.naver.com/domestic/index/KOSPI/price",
    "^KQ11": "https://stock.naver.com/domestic/index/KOSDAQ/price",
    "229200.KS": "https://stock.naver.com/domestic/index/KPI200/price",
    "KRW=X": "https://stock.naver.com/marketindex/exchange/FX_USDKRW/price",
    "JPYKRW=X": "https://stock.naver.com/marketindex/exchange/FX_JPYKRW/price",
    "^TNX": "https://www.investing.com/rates-bonds/u.s.-10-year-bond-yield",
    "^TYX": "https://www.investing.com/rates-bonds/u.s.-30-year-bond-yield",
    "DX-Y.NYB": "https://www.investing.com/currencies/us-dollar-index",
    "CL=F": "https://www.investing.com/commodities/crude-oil",
    "GC=F": "https://stock.naver.com/marketindex/metals/M04020000/price",
    "SI=F": "https://www.investing.com/commodities/silver",
    "HG=F": "https://www.investing.com/commodities/copper",
    "BTC-USD": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC",
    "ETH-USD": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-ETH",
    "XRP-USD": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-XRP",
    "SOL-USD": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-SOL",
}


def render_metric_card(col, label, value_text, delta_text, url):
    """st.metric과 비슷하게 생겼지만, 클릭하면 새 창으로 해당 지표의 상세 시세 사이트가 열리는 카드"""
    if delta_text and delta_text.startswith("+"):
        delta_color = "#09ab3b"
    elif delta_text and delta_text.startswith("-"):
        delta_color = "#ff2b2b"
    else:
        delta_color = "#888"
    delta_html = f'<div style="font-size:0.85rem;color:{delta_color};margin-top:2px;">{delta_text}</div>' if delta_text else ""
    html = f'''
    <a href="{url}" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;">
      <div style="border:1px solid rgba(128,128,128,0.25);border-radius:8px;padding:10px 14px;margin-bottom:8px;">
        <div style="font-size:0.8rem;color:#888;">{label}</div>
        <div style="font-size:1.5rem;font-weight:600;">{value_text}</div>
        {delta_html}
      </div>
    </a>
    '''
    col.markdown(html, unsafe_allow_html=True)


def show_row(items):
    """items: [(라벨, 티커, 값 포맷 함수), ...] 형태의 리스트를 받아 한 줄에 나란히 표시하는 함수"""
    cols = st.columns(len(items))
    for col, (label, ticker, fmt) in zip(cols, items):
        price, change = get_price_with_day_change(ticker)
        if price is None:
            col.metric(label, "조회 실패")
            continue
        delta = f"{change:+.2f}%" if change is not None else None
        url = INDICATOR_LINKS.get(ticker)
        if url:
            render_metric_card(col, label, fmt(price), delta, url)
        else:
            col.metric(label, fmt(price), delta)


st.subheader("미국")
show_row([
    ("S&P 500", "^GSPC", lambda v: f"{v:,.2f}"),
    ("나스닥 종합", "^IXIC", lambda v: f"{v:,.2f}"),
    ("다우존스", "^DJI", lambda v: f"{v:,.2f}"),
    ("필라델피아 반도체", "^SOX", lambda v: f"{v:,.2f}"),
    ("나스닥 100", "^NDX", lambda v: f"{v:,.2f}"),
])

st.divider()
st.subheader("한국")
show_row([
    ("코스피", "^KS11", lambda v: f"{v:,.2f}"),
    ("코스닥", "^KQ11", lambda v: f"{v:,.2f}"),
    ("코스피200 (KODEX 200)", "229200.KS", lambda v: f"{v:,.2f}"),
])

st.divider()
st.subheader("지표")
st.caption("환율 · 금리")
show_row([
    ("원/달러 환율", "KRW=X", lambda v: f"{v:,.2f}"),
    ("원/100엔 환율", "JPYKRW=X", lambda v: f"{v * 100:,.2f}"),
    ("미국 국채 10년 금리(%)", "^TNX", lambda v: f"{v:,.3f}"),
    ("미국 국채 30년 금리(%)", "^TYX", lambda v: f"{v:,.3f}"),
    ("달러 인덱스", "DX-Y.NYB", lambda v: f"{v:,.2f}"),
])

st.write("")
st.caption("에너지 · 금속")
show_row([
    ("WTI 유가", "CL=F", lambda v: f"{v:,.2f}"),
    ("국제 금", "GC=F", lambda v: f"{v:,.1f}"),
    ("국제 은", "SI=F", lambda v: f"{v:,.2f}"),
    ("구리", "HG=F", lambda v: f"{v:,.3f}"),
])

st.divider()
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
        url = INDICATOR_LINKS.get(ticker)
        if url:
            render_metric_card(col, label, value_text, delta, url)
        else:
            col.metric(label, value_text, delta)


show_crypto_row([
    ("비트코인", "BTC-USD"),
    ("이더리움", "ETH-USD"),
    ("리플", "XRP-USD"),
    ("솔라나", "SOL-USD"),
])
