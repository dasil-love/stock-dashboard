"""
급등주 스캐너 (모멘텀 TOP 20)
미국/한국 주요 종목들을 한 번에 스캔해서 RSI가 높은(최근 상승 모멘텀이 강한) 상위 20개를 찾습니다.
"""

import streamlit as st
import pandas as pd
from utils import US_STOCK_UNIVERSE, KR_TICKERS, get_kr_code_to_name_map, scan_momentum, style_negative_returns

st.set_page_config(page_title="급등주 스캐너", layout="wide")

st.title("급등주 스캐너 (모멘텀 TOP 20)")
st.caption("RSI(14)가 높을수록 최근 상승 모멘텀이 강한 종목입니다. 70 이상은 '과열' 구간으로도 해석됩니다.")
st.caption("스캔은 시간이 좀 걸릴 수 있고, 한 번 스캔한 결과는 30분간 저장되어 재방문 시 빠르게 뜹니다.")


def render_result(df, name_map=None):
    if df.empty:
        st.warning("조건에 맞는 종목을 찾지 못했습니다.")
        return

    display_df = df.copy()
    if name_map:
        display_df.insert(1, "종목명", display_df["티커"].map(lambda t: name_map.get(t, "")))
    display_df.insert(0, "순위", range(1, len(display_df) + 1))
    display_df["현재가"] = display_df["현재가"].map(lambda v: f"{v:,.2f}")
    display_df["RSI(14)"] = display_df["RSI(14)"].map(lambda v: f"{v:.1f}")
    display_df["오늘 변동률(%)"] = display_df["오늘 변동률(%)"].map(
        lambda v: f"{v:+.2f}%" if pd.notna(v) else "-"
    )
    st.dataframe(style_negative_returns(display_df), width="stretch", hide_index=True)


st.divider()
st.subheader("미국 (주요 대형·중형주 중)")
if st.button("미국 급등주 스캔하기"):
    with st.spinner("미국 주요 종목 스캔 중..."):
        us_result = scan_momentum(US_STOCK_UNIVERSE, ascending=False, top_n=20)
    render_result(us_result)

st.divider()
st.subheader("한국 (KRX300 중)")
if st.button("한국 급등주 스캔하기"):
    with st.spinner("한국 KRX300 종목 스캔 중 (종목 수가 많아 1~2분 걸릴 수 있어요)..."):
        kr_tickers = list(KR_TICKERS.values())
        kr_result = scan_momentum(kr_tickers, ascending=False, top_n=20)
    render_result(kr_result, name_map=get_kr_code_to_name_map())
