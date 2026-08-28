"""Corrected-status dashboard for the Taiwan Attention Signal project.

Run with: streamlit run app/streamlit_app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"
SAFE_V04_PANEL = ROOT / "data" / "processed" / "attention_weekly_panel_v04_asof_safe.csv"
SAFE_V03_PANEL = ROOT / "data" / "processed" / "attention_weekly_panel_v03_asof_safe.csv"

st.set_page_config(page_title="Taiwan Attention Signal", layout="wide")


@st.cache_data
def read_csv(path: str):
    return pd.read_csv(path)


def load_panel():
    for path in [SAFE_V04_PANEL, SAFE_V03_PANEL]:
        if path.exists():
            df = read_csv(str(path))
            if "week" in df.columns:
                df["week"] = pd.to_datetime(df["week"])
            return path, df
    return None, None


def show_status():
    st.title("Taiwan Attention Momentum Signal")
    if any(path.exists() for path in [SAFE_V04_PANEL, SAFE_V03_PANEL]):
        st.warning("Legacy headline results are superseded / invalidated for predictive interpretation.")
    else:
        st.warning(
            "Legacy headline results are superseded / invalidated for predictive interpretation. "
            "Corrected as-of-safe empirical results have not been regenerated in this checkout "
            "because real data/raw and data/processed inputs are missing."
        )
    st.markdown(
        "`observation_period_start` -> `observation_period_end` -> `available_at` -> "
        "`signal_date` -> `first_tradeable_at` -> `return_start` -> `return_end`"
    )


def show_panel_summary():
    path, panel = load_panel()
    st.header("As-Of-Safe Panel")
    if panel is None:
        st.info("No as-of-safe panel found. Run the corrected pipeline with real raw data.")
        return
    st.caption(str(path.relative_to(ROOT)))
    cols = st.columns(4)
    cols[0].metric("Rows", f"{len(panel):,}")
    cols[1].metric("Stocks", panel["stock_id"].nunique() if "stock_id" in panel.columns else "n/a")
    cols[2].metric("Start", panel["week"].min().date() if "week" in panel.columns else "n/a")
    cols[3].metric("End", panel["week"].max().date() if "week" in panel.columns else "n/a")
    st.dataframe(panel.head(200), use_container_width=True)


def show_tables():
    st.header("Provenance And Comparisons")
    for fname in [
        "legacy_results_provenance.csv",
        "panel_provenance_asof_safe.csv",
        "asof_safe_legacy_comparison.csv",
        "caar_event_summary_asof_safe.csv",
        "v03_fama_macbeth_summary_asof_safe.csv",
        "v04_regression_with_chips_summary_asof_safe.csv",
    ]:
        path = TABLES_DIR / fname
        if not path.exists():
            st.caption(f"Missing: {fname}")
            continue
        st.subheader(fname)
        st.dataframe(read_csv(str(path)), use_container_width=True)


def show_figures():
    st.header("As-Of-Safe Figures")
    figs = sorted(FIGURES_DIR.glob("*_asof_safe.png"))
    if not figs:
        st.info("No as-of-safe figures found.")
        return
    for fig in figs:
        st.subheader(fig.name)
        st.image(str(fig))


def main():
    show_status()
    page = st.sidebar.radio("Page", ["Panel", "Tables", "Figures"])
    if page == "Panel":
        show_panel_summary()
    elif page == "Tables":
        show_tables()
    else:
        show_figures()


if __name__ == "__main__":
    main()
