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

st.set_page_config(page_title="投資人注意力與動能研究 | Taiwan Attention Signal", layout="wide")


@st.cache_data
def load_panel():
    df = pd.read_csv(PANEL_PATH, parse_dates=["week"])
    df["stock_id"] = df["stock_id"].astype(str)
    return df


@st.cache_data
def load_csv_if_exists(path: Path):
    return pd.read_csv(path) if path.exists() else None


def page_research_overview():
    # 1. 一句話定位
    st.header("🔍 投資人搜尋關注，是否會強化原本已存在的股價動能？")
    st.caption("本頁是給第一次打開這個專案的人看的——不需要先懂統計方法")

    st.info(
        "**一句話**：研究投資人搜尋關注，是否會強化原本已存在的股價動能。"
    )

    # 2. 一個具體例子
    st.markdown("#### 一個具體例子")
    ex1, ex2 = st.columns(2)
    with ex1:
        st.markdown(
            "**股票 A**\n\n"
            "- 最近 8 週：📈 已上漲\n"
            "- Google 搜尋量：🔥 突然飆升\n"
        )
    with ex2:
        st.markdown(
            "**股票 B**\n\n"
            "- 最近 8 週：📈 同樣已上漲\n"
            "- Google 搜尋量：➖ 沒有明顯變化\n"
        )
    st.caption("（A、B 為根據下方雙重排序方法建構的示意情境，非真實股票代號、非投資建議）")

    # 3. 研究問題
    st.markdown("#### 研究問題")
    st.markdown("兩檔近期都在上漲的股票，其中一檔突然受到大量搜尋，接下來的短期價格延續是否會更明顯？")

    # 4/5. 資料與比較方法（一行帶過，細節在完整版）
    st.markdown("#### 用什麼資料、怎麼比較")
    st.markdown(
        "50 檔台股大型權值股，2021–2026 年週資料。Google Trends 搜尋量 + FinMind 股價與三大法人買賣超。"
        "把股票依「過去是否上漲」與「搜尋熱度是否飆升」交叉分組，比較各組後續報酬。"
    )

    # 6. 研究發現
    st.markdown("#### 研究發現")
    st.markdown(
        "在目前樣本中，高動能且高搜尋關注的股票，後續短期報酬延續相對較強；"
        "但搜尋熱度單獨使用時，不是穩定的預測訊號。"
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**觀察一**")
        st.markdown("像股票 A（上漲＋高關注）這組的後續累積報酬約 **+30.8%**；像股票 B（上漲＋低關注）這組統計上與零無異（p=0.50）。")
    with col2:
        st.markdown("**觀察二**")
        st.markdown("控制「過去報酬」後，這個關聯縮小約 36% 但沒有消失——顯示這不只是動能本身的重複計算，而可能是動能與注意力的交互關係。")
    with col3:
        st.markdown("**觀察三**")
        st.markdown("控制三大法人買賣超後，這個關聯幾乎不變（相關性 \\|r\\|≤0.05）——目前樣本中不易用法人籌碼解釋掉這個現象。")

    # 7. 一張最重要的圖
    st.markdown("#### 最重要的一張圖：同樣是近期上漲的股票，搜尋關注增加後，後續報酬是否更強？")
    sort_fig = FIGURES_DIR / "v03_double_sort_heatmap_4w.png"
    if sort_fig.exists():
        st.image(str(sort_fig))
    st.caption(
        "**圖表在比較什麼**：股票依「過去 4 週報酬」（輸家/中性/贏家）與「搜尋熱度」（低/中/高）交叉分成 9 組，"
        "數字為各組未來 4 週平均超額報酬。"
        "**看到什麼**：只有「贏家 × 高關注」這一格明顯突出（+3.28%），其餘格子接近 0 或負值，"
        "這是本研究樣本與模型設定下觀察到的統計關聯。"
        "**不能推論什麼**：不能證明搜尋熱度造成股價上漲（這是統計關聯，不是因果證據）；"
        "不能保證未來樣本仍有相同結果；不能直接把這個關聯轉換成買賣訊號；"
        "也不能將統計顯著等同於實際可交易的獲利。"
    )

    caar_fig = FIGURES_DIR / "caar_attention_z2.png"
    if caar_fig.exists():
        with st.expander("延伸圖表：事件研究 CAAR（注意力異常事件後的累積異常報酬）"):
            st.image(str(caar_fig))

    # 8. 研究限制 + 不能推論（明確分點，避免讀者只看到正向結果）
    st.markdown("#### 這個研究不能告訴你什麼")
    st.warning(
        "- 不能證明搜尋熱度會**造成**股價上漲——本研究只驗證統計關聯，不是因果關係。\n"
        "- 不能保證未來樣本仍會出現相同結果——樣本僅涵蓋 50 檔大型權值股、"
        "2021–2026 多為多頭的期間。\n"
        "- 不能直接把研究係數轉換成買賣訊號——未模擬交易成本、滑價與放空限制。\n"
        "- 不能將統計顯著等同於實際可交易的獲利——顯著不代表獲利穩定或可執行。\n\n"
        "完整限制見 `docs/limitations.md`。"
    )

    # 三個專案的分工
    with st.expander("這個專案跟另外兩個台股專案有什麼不同？"):
        st.markdown(
            "- **taiwan-stock-analyzer**：用來查看與分析台股（個股、技術面、因子）。\n"
            "- **stock-ai-project**：用來執行每日推薦、追蹤與 LINE 通知。\n"
            "- **taiwan-attention-momentum-signal（本專案）**：用來研究「投資人搜尋關注是否會改變既有價格趨勢」——"
            "提出問題、整合資料、建立方法、驗證假說、誠實呈現限制，不是即時交易或股票推薦工具。"
        )

    # 9. 完整方法入口（公式/迴歸規格/執行指令都在這裡，不放第一屏）
    st.markdown(
        "**完整版**：[README（英文）](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/README.md) · "
        "[README_zh（中文，含完整研究演進）](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/README_zh.md) · "
        "[方法論（Fama-MacBeth／迴歸規格／公式）](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/docs/methodology.md) · "
        "[研究限制](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/docs/limitations.md) · "
        "[如何重現（執行指令）](https://github.com/Harry970417/taiwan-attention-momentum-signal/blob/main/docs/REPRODUCIBILITY_GUIDE.md)"
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
    st.title("投資人注意力與動能研究")
    st.caption("Taiwan Attention Signal · 學術實證研究，結果僅供研究參考，非投資建議")

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
