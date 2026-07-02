"""Plot search-volume trend and search-volume-vs-price overlay for each stock."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

DATA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
FIGURES = Path(__file__).resolve().parent.parent / "results" / "figures"

STOCK_NAMES = {
    "2330": "台積電",
    "2454": "聯發科",
    "2317": "鴻海",
    "2308": "台達電",
    "2603": "長榮",
}


def plot_trend(stock_id: str, name: str):
    svi = pd.read_csv(DATA_RAW / f"trends_{stock_id}.csv", index_col=0, parse_dates=True)
    svi.columns = ["SVI"]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(svi.index, svi["SVI"], color="tab:blue")
    ax.set_title(f"{stock_id} {name} - Google Trends Search Volume Index (weekly)")
    ax.set_xlabel("Date")
    ax.set_ylabel("SVI (0-100)")
    fig.tight_layout()
    fig.savefig(FIGURES / f"trend_{stock_id}.png", dpi=150)
    plt.close(fig)


def plot_trend_vs_price(stock_id: str, name: str):
    svi = pd.read_csv(DATA_RAW / f"trends_{stock_id}.csv", index_col=0, parse_dates=True)
    svi.columns = ["SVI"]
    price = pd.read_csv(DATA_RAW / f"price_{stock_id}.csv", parse_dates=["date"]).set_index("date")

    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax1.plot(svi.index, svi["SVI"], color="tab:blue", label="SVI (search volume)")
    ax1.set_ylabel("SVI (0-100)", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(price.index, price["close"], color="tab:red", alpha=0.7, label="Close price")
    ax2.set_ylabel("Close price (TWD)", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    ax1.set_title(f"{stock_id} {name} - Search Volume vs. Close Price")
    fig.tight_layout()
    fig.savefig(FIGURES / f"trend_vs_price_{stock_id}.png", dpi=150)
    plt.close(fig)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    for stock_id, name in STOCK_NAMES.items():
        trends_path = DATA_RAW / f"trends_{stock_id}.csv"
        price_path = DATA_RAW / f"price_{stock_id}.csv"
        if not trends_path.exists():
            print(f"Skip {stock_id}: no trends data")
            continue
        plot_trend(stock_id, name)
        if price_path.exists():
            plot_trend_vs_price(stock_id, name)
        print(f"{stock_id}: figures saved")


if __name__ == "__main__":
    main()
