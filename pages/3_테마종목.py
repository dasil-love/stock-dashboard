"""
테마종목 페이지
미국/한국 관심 섹터를 고르면, 그 섹터에 속한 종목들의 현재가/PER/RSI/기간별 변동률을 한 표에서 봅니다.
매수/매도 판단에 참고할 수 있는 지표만 보여줄 뿐, 투자 조언을 제공하지는 않습니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from utils import (
    KR_SECTOR_STOCKS,
    US_SECTOR_STOCKS,
    resolve_kr_ticker,
    calculate_rsi,
    calculate_period_returns,
    style_negative_returns,
    set_korean_font,
)

st.set_page_config(page_title="테마종목", layout="wide")
set_korean_font()  # OS에 맞는 한글 폰트를 자동으로 찾아서 적용 (윈도우/리눅스 모두 대응)

st.title("테마종목")
st.caption("섹터를 고르면 관련 종목의 현재가/PER/RSI/기간별 변동률을 보여줍니다. 매수·매도 결정에 참고할 지표만 제공하며, 투자 조언은 아닙니다.")

RETURN_COLUMNS = ["5일", "1개월", "6개월", "1년", "5년"]


@st.cache_data(ttl=1800, show_spinner=False)
def load_sector_table(tickers, name_map):
    """섹터에 속한 종목들의 현재가/PER/RSI/기간별 변동률을 한 번에 계산하는 함수"""
    unique_tickers = list(dict.fromkeys(tickers))
    data = yf.download(unique_tickers, period="5y", interval="1d", group_by="ticker", threads=True, progress=False)

    rows = []
    for ticker in unique_tickers:
        try:
            close = data[ticker]["Close"].dropna()
        except (KeyError, TypeError):
            continue
        if close.empty:
            continue

        try:
            info = yf.Ticker(ticker).info
        except Exception:
            info = {}

        rsi_series = calculate_rsi(close)
        rsi_value = rsi_series.iloc[-1] if not rsi_series.empty else None

        row = {
            "티커": ticker,
            "종목명": name_map.get(ticker, ticker),
            "현재가": close.iloc[-1],
            "PER": info.get("trailingPE"),
            "RSI(14)": rsi_value,
        }
        row.update(calculate_period_returns(close))
        rows.append(row)

    return pd.DataFrame(rows)


def render_sector_table(df):
    if df.empty:
        st.warning("데이터를 찾을 수 없습니다.")
        return

    display_df = df.copy()
    display_df["현재가"] = display_df["현재가"].map(lambda v: f"{v:,.2f}")
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


def render_return_heatmap(df, sector_name):
    """종목 x 기간(5일~5년) 수익률을 색깔로 한눈에 보여주는 히트맵"""
    st.subheader(f"{sector_name} 기간별 수익률 히트맵")
    values = df[RETURN_COLUMNS].astype(float)
    # 색상은 -30%~+30% 구간에서 가장 진하게, 그 밖은 값은 그대로 표시하되 색은 포화시킴 (한두 종목의 극단치가 전체 색을 밀어버리는 것 방지)
    clipped = values.clip(lower=-30, upper=30)

    cmap = plt.get_cmap("RdYlGn")
    norm = plt.Normalize(vmin=-30, vmax=30)

    NEON = "#F5FF00"  # 5년 수익률 300% 이상인 셀의 "글자색"으로 쓸 형광색
    five_year_idx = RETURN_COLUMNS.index("5년")

    fig, ax = plt.subplots(figsize=(9, max(2.5, len(df) * 0.42)))
    im = ax.imshow(clipped.values, cmap=cmap, norm=norm, aspect="auto")  # 바탕색은 원래 데이터 그대로

    ax.set_xticks(range(len(RETURN_COLUMNS)))
    ax.set_xticklabels(RETURN_COLUMNS)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["종목명"])

    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            val = values.values[i, j]
            if pd.notna(val):
                is_neon = j == five_year_idx and val >= 300
                if is_neon:
                    text_color = NEON
                else:
                    text_color = "white" if abs(val) >= 25 else "black"
                ax.text(j, i, f"{val:+.1f}%", ha="center", va="center", fontsize=8, color=text_color,
                         fontweight="bold" if is_neon else "normal")

    fig.colorbar(im, ax=ax, label="수익률(%) (±30% 기준 색상 포화, 5년 300%+는 글자가 형광색)")
    fig.tight_layout()
    st.pyplot(fig)


def render_rsi_scatter(df, sector_name):
    """RSI(과열도) vs 1개월 수익률 산점도. 오른쪽 위=많이 올랐고 과열, 오른쪽 아래=많이 올랐지만 아직 안 과열"""
    st.subheader(f"{sector_name} RSI vs 1개월 수익률")
    plot_df = df.dropna(subset=["RSI(14)", "1개월"])
    if plot_df.empty:
        st.info("표시할 데이터가 부족합니다.")
        return

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(plot_df["RSI(14)"], plot_df["1개월"], s=90, color="#4C78A8", edgecolors="white", zorder=3)
    for _, row in plot_df.iterrows():
        ax.annotate(row["종목명"], (row["RSI(14)"], row["1개월"]), fontsize=8, xytext=(5, 5), textcoords="offset points")

    ax.axvline(70, color="red", linestyle="--", alpha=0.4, label="과열(70)")
    ax.axvline(30, color="blue", linestyle="--", alpha=0.4, label="과매도(30)")
    ax.axhline(0, color="gray", linestyle="-", alpha=0.3)
    ax.set_xlabel("RSI(14) - 오른쪽일수록 과열")
    ax.set_ylabel("1개월 수익률(%) - 위로 갈수록 최근 많이 상승")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)


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
        table = load_sector_table(tickers, name_map)

    render_sector_table(table)

    if not table.empty:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            render_return_heatmap(table, sector)
        with col2:
            render_rsi_scatter(table, sector)
