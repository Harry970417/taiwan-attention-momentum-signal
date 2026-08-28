"""As-of-safe date contract for weekly Google Trends signals.

Google Trends long-range interest-over-time data is aggregated in UTC and
pytrends labels the weekly row by the weekly bucket start. Historical
release timestamps for each bucket are not available in this project, so
the research contract applies a conservative full-week delay before a row
can become a signal.
"""
from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

GOOGLE_TRENDS_WEEK_START_WEEKDAY = 6  # Sunday, pandas: Monday=0.
OBSERVATION_DAYS = 7
CONSERVATIVE_WEEKLY_LAG_DAYS = 14
AVAILABILITY_POLICY = "google_trends_week_start_utc_plus_one_full_week_lag"

CONTRACT_COLUMNS = [
    "observation_period_start",
    "observation_period_end",
    "available_at",
    "signal_date",
    "first_tradeable_at",
    "feature_asof_trade_date",
    "return_start",
]


def normalize_date(value) -> pd.Timestamp:
    return pd.Timestamp(value).tz_localize(None).normalize()


def _as_datetime_series(values) -> pd.Series:
    return pd.to_datetime(values).dt.tz_localize(None).dt.normalize()


def assert_google_trends_weekly_index(index: pd.DatetimeIndex) -> None:
    """Fail fast if weekly Trends labels are not the expected UTC Sundays."""
    if index.empty:
        return
    normalized = pd.DatetimeIndex(pd.to_datetime(index)).tz_localize(None).normalize()
    bad = normalized[normalized.weekday != GOOGLE_TRENDS_WEEK_START_WEEKDAY]
    if len(bad):
        sample = ", ".join(str(x.date()) for x in bad[:5])
        raise AssertionError(
            "Google Trends weekly labels must be UTC week starts (Sunday). "
            f"Unexpected labels: {sample}"
        )


def annotate_google_trends_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Return SVI plus explicit observation and availability dates.

    Accepts both legacy one-column raw files indexed by the Trends weekly
    label and newly annotated files that already carry the contract columns.
    """
    if df.empty:
        return df.copy()

    out = df.copy()
    if "isPartial" in out.columns:
        out = out.loc[~out["isPartial"].fillna(False).astype(bool)].drop(columns=["isPartial"])

    if "SVI" not in out.columns:
        numeric_cols = [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
        if not numeric_cols:
            raise ValueError("Trend data must contain an SVI column or one numeric SVI series.")
        out = out.rename(columns={numeric_cols[0]: "SVI"})

    if "observation_period_start" in out.columns:
        obs_start = _as_datetime_series(out["observation_period_start"])
    else:
        obs_start = pd.Series(pd.to_datetime(out.index), index=out.index).dt.tz_localize(None).dt.normalize()

    assert_google_trends_weekly_index(pd.DatetimeIndex(obs_start))

    out = out.reset_index(drop=True).copy()
    out["observation_period_start"] = obs_start.to_numpy()
    out["observation_period_end"] = out["observation_period_start"] + pd.Timedelta(days=OBSERVATION_DAYS - 1)
    out["available_at"] = out["observation_period_start"] + pd.Timedelta(days=CONSERVATIVE_WEEKLY_LAG_DAYS)
    out["signal_date"] = out["available_at"]
    out["availability_policy"] = AVAILABILITY_POLICY
    out = out.sort_values("observation_period_start").set_index("observation_period_start", drop=False)
    return out[["SVI", "observation_period_start", "observation_period_end", "available_at", "signal_date", "availability_policy"]]


def first_at_or_after(index: pd.DatetimeIndex, target) -> pd.Timestamp | None:
    idx = pd.DatetimeIndex(pd.to_datetime(index)).sort_values()
    target = normalize_date(target)
    cand = idx[idx >= target]
    return cand[0] if len(cand) else None


def last_at_or_before(index: pd.DatetimeIndex, target) -> pd.Timestamp | None:
    idx = pd.DatetimeIndex(pd.to_datetime(index)).sort_values()
    target = normalize_date(target)
    cand = idx[idx <= target]
    return cand[-1] if len(cand) else None


def last_before(index: pd.DatetimeIndex, target) -> pd.Timestamp | None:
    idx = pd.DatetimeIndex(pd.to_datetime(index)).sort_values()
    target = normalize_date(target)
    cand = idx[idx < target]
    return cand[-1] if len(cand) else None


def window_return(price: pd.Series, start, end) -> float | None:
    start = normalize_date(start)
    end = normalize_date(end)
    if start not in price.index or end not in price.index or end <= start:
        return None
    p0, p1 = price.loc[start], price.loc[end]
    if pd.isna(p0) or pd.isna(p1) or p0 == 0:
        return None
    return float(p1 / p0 - 1)


def trailing_window_return(price: pd.Series, end, n_weeks: int) -> float | None:
    idx = pd.DatetimeIndex(price.index)
    end_date = last_at_or_before(idx, end)
    if end_date is None:
        return None
    start_date = last_at_or_before(idx, end_date - pd.Timedelta(weeks=n_weeks))
    if start_date is None:
        return None
    return window_return(price, start_date, end_date)


def forward_window(price: pd.Series, return_start, n_weeks: int) -> tuple[pd.Timestamp | None, float | None]:
    idx = pd.DatetimeIndex(price.index)
    start_date = first_at_or_after(idx, return_start)
    if start_date is None:
        return None, None
    end_date = first_at_or_after(idx, start_date + pd.Timedelta(weeks=n_weeks))
    if end_date is None:
        return None, None
    return end_date, window_return(price, start_date, end_date)


def add_trailing_attention_features(svi: pd.DataFrame) -> pd.DataFrame:
    """Compute attention features with trailing, non-centered SVI windows."""
    out = annotate_google_trends_weekly(svi)
    out["SVI_MA52"] = out["SVI"].rolling(52, min_periods=26, center=False).mean()
    out["SVI_STD52"] = out["SVI"].rolling(52, min_periods=26, center=False).std()
    out["SVI_window_n"] = out["SVI"].rolling(52, min_periods=26, center=False).count()
    out["z_window_end"] = out["observation_period_end"]
    out["attention_shock"] = out["SVI"] / out["SVI_MA52"] - 1
    out["attention_z"] = (out["SVI"] - out["SVI_MA52"]) / out["SVI_STD52"]
    return out


def _assert_mask(df: pd.DataFrame, mask: pd.Series, message: str, columns: Iterable[str]) -> None:
    if bool(mask.fillna(False).any()):
        cols = [c for c in columns if c in df.columns]
        sample = df.loc[mask, cols].head(5).to_dict("records")
        raise AssertionError(f"{message}. Offending rows: {sample}")


def assert_no_lookahead_panel(panel: pd.DataFrame) -> None:
    """Assert that every signal and return window respects the as-of contract."""
    missing = [c for c in CONTRACT_COLUMNS if c not in panel.columns]
    if missing:
        raise AssertionError(f"Panel is missing as-of contract columns: {missing}")

    df = panel.copy()
    for col in CONTRACT_COLUMNS + [c for c in panel.columns if c.startswith("return_end_") or c == "z_window_end"]:
        if col in df.columns:
            df[col] = _as_datetime_series(df[col])

    date_cols = CONTRACT_COLUMNS + ["z_window_end"]
    _assert_mask(
        df,
        df["observation_period_start"].dt.weekday != GOOGLE_TRENDS_WEEK_START_WEEKDAY,
        "Google Trends observation_period_start must be Sunday UTC",
        date_cols,
    )
    _assert_mask(
        df,
        df["observation_period_end"] != df["observation_period_start"] + pd.Timedelta(days=OBSERVATION_DAYS - 1),
        "Google Trends observation period must span exactly seven UTC dates",
        date_cols,
    )
    _assert_mask(
        df,
        df["available_at"] < df["observation_period_start"] + pd.Timedelta(days=CONSERVATIVE_WEEKLY_LAG_DAYS),
        "Trend row is available before the conservative full-week lag",
        date_cols,
    )
    _assert_mask(
        df,
        df["signal_date"] < df["available_at"],
        "Signal date precedes available_at",
        date_cols,
    )
    _assert_mask(
        df,
        df["first_tradeable_at"] < df["signal_date"],
        "First tradeable date precedes signal_date",
        date_cols,
    )
    _assert_mask(
        df,
        df["feature_asof_trade_date"] >= df["first_tradeable_at"],
        "Feature as-of trade date must be strictly before the first tradeable date",
        date_cols,
    )
    _assert_mask(
        df,
        df["return_start"] < df["first_tradeable_at"],
        "Return start precedes first_tradeable_at",
        date_cols,
    )
    _assert_mask(
        df,
        df["return_start"] <= df["observation_period_end"],
        "Forward return starts before the observed Trends week is complete",
        date_cols,
    )
    if "z_window_end" in df.columns:
        _assert_mask(
            df,
            df["z_window_end"] > df["observation_period_end"],
            "attention_z uses SVI data after the current observation period",
            date_cols,
        )

    for col in df.columns:
        match = re.fullmatch(r"return_end_(\d+)w", col)
        if not match:
            continue
        weeks = int(match.group(1))
        _assert_mask(
            df,
            df[col].notna() & (df[col] < df["return_start"] + pd.Timedelta(weeks=weeks)),
            f"{col} ends before its stated forward horizon",
            ["stock_id", "week", "return_start", col],
        )
