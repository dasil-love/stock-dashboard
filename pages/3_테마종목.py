"""
테마종목 페이지
미국/한국 관심 섹터를 고르면, 그 섹터에 속한 종목들의 현재가/PER/RSI/기간별 변동률을 한 표에서 봅니다.
매수/매도 판단에 참고할 수 있는 지표만 보여줄 뿐, 투자 조언을 제공하지는 않습니다.
"""

import streamlit as st
import pandas as pd
from utils import (
    KR_SECTOR_STOCKS,
    KR_SECTOR_ETF_NAMES,
    US_SECTOR_STOCKS,
    resolve_kr_ticker,
    style_negative_returns,
    set_korean_font,
    RETURN_COLUMNS,
    compute_return_rsi_table,
    render_return_heatmap,
    render_rsi_scatter,
)

# 이 섹터들은 개별 종목 수가 많아, RSI 산점도에 ETF까지 같이 넣으면 개별 종목 이름표가 잘 안 보임 -
# 히트맵에는 그대로 두고 산점도에서만 ETF를 뺌
SCATTER_HIDE_ETF_SECTORS = {"반도체", "전력설비/원자력"}

st.set_page_config(page_title="테마종목", layout="wide")
set_korean_font()  # OS에 맞는 한글 폰트를 자동으로 찾아서 적용 (윈도우/리눅스 모두 대응)

st.title("테마종목")
st.caption("섹터를 고르면 관련 종목의 현재가/PER/RSI/기간별 변동률을 보여줍니다. 매수·매도 결정에 참고할 지표만 제공하며, 투자 조언은 아닙니다.")


def render_sector_table(df):
    if df.empty:
        st.warning("데이터를 찾을 수 없습니다.")
        return

    display_df = df.copy()
    display_df["현재가"] = display_df["현재가"].map(lambda v: f"{v:,.2f}")
    if "PER" in display_df.columns:
        display_df["PER"] = display_df["PER"].map(lambda v: f"{v:.2f}" if pd.notna(v) else "N/A")
    display_df["RSI(14)"] = display_df["RSI(14)"].map(lambda v: f"{v:.1f}" if pd.notna(v) else "N/A")
    for col in RETURN_COLUMNS:
        display_df[col] = display_df[col].map(lambda v: f"{v:+.2f}%" if pd.notna(v) else "-")

    # style_negative_returns는 "수익률"/"오늘 변동률(%)" 열을 대상으로 하므로, 기간별 변동률 열도 같은 방식으로 직접 색칠
    def _color_negative(value):
        if isinstance(value, str) and value.startswith("-"):
            return "color: red"
        return ""

    styled = display_df.style.map(_color_negative, subset=RETURN_COLUMNS)
    st.dataframe(styled, width="stretch", hide_index=True)


market = st.radio("시장 선택", ["미국", "한국"], horizontal=True)

if market == "미국":
    sector = st.selectbox("섹터 선택", list(US_SECTOR_STOCKS.keys()))
    tickers = US_SECTOR_STOCKS[sector]
    name_map = {t: t for t in tickers}
else:
    sector = st.selectbox("섹터 선택", list(KR_SECTOR_STOCKS.keys()))
    names = KR_SECTOR_STOCKS[sector]
    tickers = []
    name_map = {}
    for name in names:
        ticker = resolve_kr_ticker(name)
        if ticker:
            tickers.append(ticker)
            name_map[ticker] = name

if st.button(f"{sector} 종목 조회"):
    with st.spinner(f"{sector} 섹터 {len(tickers)}개 종목 조회 중..."):
        # 한국 종목/ETF는 야후 파이낸스가 PER을 거의 안 주므로, 한국 시장에서는 PER 열 자체를 생략
        table = compute_return_rsi_table(tickers, name_map, include_per=(market == "미국"))

    render_sector_table(table)

    if not table.empty:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            render_return_heatmap(table, sector)
        with col2:
            scatter_table = table
            if market == "한국" and sector in SCATTER_HIDE_ETF_SECTORS:
                scatter_table = table[~table["종목명"].isin(KR_SECTOR_ETF_NAMES)]
            render_rsi_scatter(scatter_table, sector)
