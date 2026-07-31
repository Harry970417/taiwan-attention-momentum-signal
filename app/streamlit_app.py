"""TAS v0.2 Streamlit MVP dashboard.

Run with: venv/Scripts/streamlit run app/streamlit_app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PANEL_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_50.csv"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"

st.set_page_config(page_title="Taiwan Attention Signal (TAS) v0.2", layout="wide")


@st.cache_data
def load_panel():
    df = pd.read_csv(PANEL_PATH, parse_dates=["week"])
    df["stock_id"] = df["stock_id"].astype(str)
    return df


@st.cache_data
def load_csv_if_exists(path: Path):
    return pd.read_csv(path) if path.exists() else None


def page_research_overview():
    st.header("研究總覽")
    st.caption("本頁是給第一次打開這個專案的人看的——不需要先懂統計方法")

    st.info(
        "**30 秒版**：Google 搜尋量異常上升（投資人注意力）不是一個能獨立預測股價的訊號，"
        "而是「動能放大器」——過去已經上漲的股票，若同時出現搜尋熱度飆升，短期續漲效果更強；"
        "這個效應不是三大法人籌碼造成的假象。"
    )

    st.markdown("#### 3 分鐘版：研究是怎麼一步步修正的")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**v0.2 初步結果**")
        st.markdown("8 週異常報酬 +14.2%，統計顯著。但拆組後發現效應集中在「過去已上漲」的股票。")
    with col2:
        st.markdown("**v0.3 控制動能**")
        st.markdown("加入動能控制後係數縮小約 36%，但沒有消失，且效果隨時間拉長而擴大。")
    with col3:
        st.markdown("**v0.4 控制法人籌碼**")
        st.markdown("注意力與三大法人買賣超相關性極低（\\|r\\|≤0.05），排除法人籌碼是替代解釋。")

    caar_fig = FIGURES_DIR / "caar_attention_z2.png"
    sort_fig = FIGURES_DIR / "v03_double_sort_heatmap_4w.png"
    c1, c2 = st.columns(2)
    if caar_fig.exists():
        with c1:
            st.image(str(caar_fig), caption="事件研究：注意力異常事件後的累積異常報酬（CAAR）")
    if sort_fig.exists():
        with c2:
            st.image(str(sort_fig), caption="雙重排序：動能 × 注意力交叉分組報酬")

    st.markdown("#### 這個研究不能告訴你什麼")
    st.warning(
        "僅涵蓋 50 檔大型權值股、2021–2026 多為多頭的期間；未模擬交易成本與放空限制；"
        "不是可直接使用的交易訊號或獲利保證。完整限制見 `docs/limitations.md`。"
    )

    st.markdown(
        "**完整版**：[README（英文）](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/README.md) · "
        "[README_zh（中文，含完整研究演進）](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/README_zh.md) · "
        "[方法論](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/docs/methodology.md) · "
        "[研究限制](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/docs/limitations.md)"
    )
    st.caption("往下探索：左側「資料總覽」看資料收集狀況、「注意力雷達」看本週訊號、「個股查詢」看個股走勢、「研究結果」看完整圖表。")


def page_overview(panel: pd.DataFrame):
    st.header("資料總覽")
    collection_status = load_csv_if_exists(TABLES_DIR / "data_collection_status_50.csv")
    trends_result = load_csv_if_exists(TABLES_DIR / "google_trends_test_result_50.csv")

    n_stocks = panel["stock_id"].nunique()
    n_weeks = panel["week"].nunique()
    n_events_z2 = int(panel["is_attention_event_z2"].fillna(False).sum())
    n_events_ratio = int(panel["is_attention_event_ratio"].fillna(False).sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("成功抓取股票數", n_stocks)
    if trends_result is not None:
        success_rate = trends_result["success"].mean() * 100
        col2.metric("Google Trends 成功率", f"{success_rate:.0f}%")
    col3.metric("可用週數", n_weeks)
    col4.metric("注意力事件數 (z>2)", n_events_z2)

    st.caption(f"attention_shock>1 事件數: {n_events_ratio}")

    if collection_status is not None:
        st.subheader("資料收集狀態明細")
        st.dataframe(collection_status, use_container_width=True)
    elif trends_result is not None:
        st.subheader("Google Trends 收集狀態")
        st.dataframe(trends_result, use_container_width=True)


def page_radar(panel: pd.DataFrame):
    st.header("注意力雷達 - 最新一週 Top 20")
    latest_week = panel["week"].max()
    st.caption(f"最新資料週: {latest_week.date()}")
    wk = panel[panel["week"] == latest_week].copy()
    wk = wk.sort_values("attention_z", ascending=False).head(20)
    cols = ["stock_id", "stock_name", "attention_z", "attention_shock", "past_1w_return"]
    st.dataframe(wk[cols].rename(columns={"past_1w_return": "近1週報酬"}), use_container_width=True)


def page_stock_lookup(panel: pd.DataFrame, stock_list: pd.DataFrame):
    st.header("個股查詢")
    options = stock_list[["stock_id", "stock_name"]].drop_duplicates()
    label_map = {f"{r.stock_id} {r.stock_name}": r.stock_id for r in options.itertuples()}
    choice = st.selectbox("選擇股票", list(label_map.keys()))
    stock_id = label_map[choice]

    trends_path = RAW_DIR / f"trends_{stock_id}.csv"
    price_path = RAW_DIR / f"price_{stock_id}.csv"
    if not trends_path.exists():
        st.warning("此股票沒有可用的 Google Trends 資料")
        return

    svi = pd.read_csv(trends_path, index_col=0, parse_dates=True)
    svi.columns = ["SVI"]
    sub = panel[panel["stock_id"] == stock_id].sort_values("week")

    fig1, ax1 = plt.subplots(figsize=(9, 3.5))
    ax1.plot(svi.index, svi["SVI"], color="tab:blue")
    events = sub[sub["is_attention_event_z2"].fillna(False)]
    for _, e in events.iterrows():
        ax1.axvline(pd.Timestamp(e["week"]), color="red", alpha=0.3, linewidth=1)
    ax1.set_title(f"{stock_id} SVI 趨勢圖(紅線=注意力事件週)")
    st.pyplot(fig1)

    if price_path.exists():
        price = pd.read_csv(price_path, parse_dates=["date"]).set_index("date")
        fig2, ax2a = plt.subplots(figsize=(9, 3.5))
        ax2a.plot(svi.index, svi["SVI"], color="tab:blue", label="SVI")
        ax2a.set_ylabel("SVI", color="tab:blue")
        ax2b = ax2a.twinx()
        ax2b.plot(price.index, price["close"], color="tab:red", alpha=0.7, label="Close")
        ax2b.set_ylabel("Close price", color="tab:red")
        ax2a.set_title(f"{stock_id} 搜尋量 vs 股價")
        st.pyplot(fig2)

    st.subheader("注意力事件明細")
    st.dataframe(sub[["week", "SVI", "attention_z", "attention_shock", "future_1w_return", "future_4w_return"]],
                 use_container_width=True)


def page_research_results():
    st.header("研究結果")

    for fig_name, title in [
        ("caar_attention_z2.png", "CAAR - attention_z > 2"),
        ("caar_attention_ratio.png", "CAAR - attention_shock > 1"),
        ("caar_attention_top_decile.png", "CAAR - top decile"),
        ("ic_timeseries_attention_z.png", "IC time series"),
        ("ic_decay.png", "IC decay"),
    ]:
        path = FIGURES_DIR / fig_name
        if path.exists():
            st.subheader(title)
            st.image(str(path))

    backtest_summary = load_csv_if_exists(TABLES_DIR / "backtest_summary.csv")
    if backtest_summary is not None:
        st.subheader("Backtest Summary")
        st.dataframe(backtest_summary, use_container_width=True)
    bt_fig = FIGURES_DIR / "backtest_cumulative_return.png"
    if bt_fig.exists():
        st.image(str(bt_fig))


def main():
    st.title("Taiwan Attention Signal (TAS) v0.2")
    st.caption("研究型 MVP - 結果僅供研究參考,非投資建議")

    panel_available = PANEL_PATH.exists()
    page_options = ["研究總覽", "研究結果"]
    if panel_available:
        page_options[1:1] = ["資料總覽", "注意力雷達", "個股查詢"]
    page = st.sidebar.radio("頁面", page_options)

    if page == "研究總覽":
        page_research_overview()
        return
    if page == "研究結果":
        page_research_results()
        return

    # 以下頁面需要完整 50 檔週資料面板（data/processed/attention_weekly_panel_50.csv），
    # 該檔案未隨 repo 提交（見 README §11），需先執行 scripts/run_all.py 產生
    if not panel_available:
        st.error(f"找不到 {PANEL_PATH}，請先執行 python scripts/run_all.py（見「研究總覽」頁的重現步驟）")
        return

    panel = load_panel()
    stock_list = pd.read_csv(ROOT / "config" / "stock_list_50.csv", dtype={"stock_id": str})

    if page == "資料總覽":
        page_overview(panel)
    elif page == "注意力雷達":
        page_radar(panel)
    elif page == "個股查詢":
        page_stock_lookup(panel, stock_list)


if __name__ == "__main__":
    main()
