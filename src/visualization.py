"""Plot search-volume trend and search-volume-vs-price overlays."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from asof_contract import annotate_google_trends_weekly

matplotlib.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
FIGURES = ROOT / "results" / "figures"
CONFIG_CSV = ROOT / "config" / "stock_list_50.csv"

PLOT_STOCK_IDS = ["2330", "2454", "2317", "2308", "2603"]


def load_trends_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    if "observation_period_start" in raw.columns:
        return annotate_google_trends_weekly(raw)
    if "SVI" in raw.columns and raw.columns[0] != "SVI":
        raw = raw.set_index(pd.to_datetime(raw[raw.columns[0]]))[["SVI"]]
    else:
        raw = pd.read_csv(path, index_col=0, parse_dates=True)
        if "SVI" not in raw.columns:
            raw.columns = ["SVI"]
    return annotate_google_trends_weekly(raw)


def plot_trend(stock_id: str, name: str):
    svi = load_trends_csv(DATA_RAW / f"trends_{stock_id}.csv")

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(svi["observation_period_start"], svi["SVI"], color="tab:blue")
    ax.set_title(f"{stock_id} {name} - Google Trends SVI (weekly, observation week)")
    ax.set_xlabel("Observation period start")
    ax.set_ylabel("SVI")
    fig.tight_layout()
    fig.savefig(FIGURES / f"trend_{stock_id}_asof_safe.png", dpi=150)
    plt.close(fig)


def plot_trend_vs_price(stock_id: str, name: str):
    svi = load_trends_csv(DATA_RAW / f"trends_{stock_id}.csv")
    price = pd.read_csv(DATA_RAW / f"price_{stock_id}.csv", parse_dates=["date"]).set_index("date")

    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax1.plot(svi["observation_period_start"], svi["SVI"], color="tab:blue", label="SVI")
    ax1.set_ylabel("SVI", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(price.index, price["close"], color="tab:red", alpha=0.7, label="Close")
    ax2.set_ylabel("Close price", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    ax1.set_title(f"{stock_id} {name} - Search Volume vs. Close Price")
    fig.tight_layout()
    fig.savefig(FIGURES / f"trend_vs_price_{stock_id}_asof_safe.png", dpi=150)
    plt.close(fig)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    if CONFIG_CSV.exists():
        stocks = pd.read_csv(CONFIG_CSV, dtype={"stock_id": str})
        name_map = dict(zip(stocks["stock_id"], stocks["stock_name"]))
    else:
        name_map = {}

    for stock_id in PLOT_STOCK_IDS:
        trends_path = DATA_RAW / f"trends_{stock_id}.csv"
        price_path = DATA_RAW / f"price_{stock_id}.csv"
        if not trends_path.exists():
            print(f"Skip {stock_id}: no trends data")
            continue
        name = name_map.get(stock_id, stock_id)
        plot_trend(stock_id, name)
        if price_path.exists():
            plot_trend_vs_price(stock_id, name)
        print(f"{stock_id}: as-of-safe figures saved")


if __name__ == "__main__":
    main()
