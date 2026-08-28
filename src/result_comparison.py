"""Compare legacy results against corrected as-of-safe outputs."""
from __future__ import annotations

from pathlib import Path
import hashlib

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = ROOT / "results" / "tables"
PROCESSED_DIR = ROOT / "data" / "processed"

COMPARISONS = [
    {
        "name": "event_study_caar",
        "legacy": "caar_event_summary.csv",
        "corrected": "caar_event_summary_asof_safe.csv",
        "keys": ["event_definition"],
        "metrics": [
            "n_events_raw",
            "n_events_after_nonoverlap_filter",
            "CAR_mean_at_final_window",
            "t_stat",
            "p_value",
            "n_events_used_in_test",
        ],
    },
    {
        "name": "fama_macbeth_momentum_control",
        "legacy": "v03_fama_macbeth_summary.csv",
        "corrected": "v03_fama_macbeth_summary_asof_safe.csv",
        "keys": ["model", "horizon"],
        "metrics": ["coefficient", "t_stat", "p_value", "n_weeks"],
    },
    {
        "name": "residual_attention_ic",
        "legacy": "v03_residual_ic_summary.csv",
        "corrected": "v03_residual_ic_summary_asof_safe.csv",
        "keys": ["factor", "horizon"],
        "metrics": ["IC_mean", "ICIR", "t_stat", "p_value", "n_weeks"],
    },
    {
        "name": "institutional_flow_regression",
        "legacy": "v04_regression_with_chips_summary.csv",
        "corrected": "v04_regression_with_chips_summary_asof_safe.csv",
        "keys": ["model", "horizon"],
        "metrics": ["coefficient", "t_stat", "p_value", "n_weeks"],
    },
    {
        "name": "institutional_flow_interactions",
        "legacy": "v04_interaction_model_summary.csv",
        "corrected": "v04_interaction_model_summary_asof_safe.csv",
        "keys": ["horizon", "term"],
        "metrics": ["coefficient", "t_stat", "p_value", "n_weeks"],
    },
]

GENERATED_ARTIFACTS = {
    "results/tables/asof_safe_legacy_comparison.csv",
    "results/tables/legacy_results_provenance.csv",
    "results/tables/panel_provenance_asof_safe.csv",
    "results/tables/panel_coverage_manifest_asof_safe.csv",
}

NON_EVIDENCE_ARTIFACTS = {
    "results/tables/google_trends_test_result_50.csv",
}

LEGACY_EVIDENCE = [
    {
        "claim_area": "event_study_caar",
        "artifact_type": "table",
        "legacy": "results/tables/caar_event_summary.csv",
        "corrected": "results/tables/caar_event_summary_asof_safe.csv",
    },
    {
        "claim_area": "attention_ic",
        "artifact_type": "table",
        "legacy": "results/tables/ic_summary.csv",
        "corrected": None,
        "not_regenerated_reason": "legacy IC headline is invalidated; no corrected IC table has been regenerated yet",
    },
    {
        "claim_area": "fama_macbeth_momentum_control",
        "artifact_type": "table",
        "legacy": "results/tables/v03_fama_macbeth_summary.csv",
        "corrected": "results/tables/v03_fama_macbeth_summary_asof_safe.csv",
    },
    {
        "claim_area": "matched_event_study",
        "artifact_type": "table",
        "legacy": "results/tables/v03_matched_event_summary.csv",
        "corrected": None,
        "not_regenerated_reason": "legacy matched-event headline is invalidated; no corrected matched-event table has been regenerated yet",
    },
    {
        "claim_area": "residual_attention_ic",
        "artifact_type": "table",
        "legacy": "results/tables/v03_residual_ic_summary.csv",
        "corrected": "results/tables/v03_residual_ic_summary_asof_safe.csv",
    },
    {
        "claim_area": "institutional_flow_regression",
        "artifact_type": "table",
        "legacy": "results/tables/v04_regression_with_chips_summary.csv",
        "corrected": "results/tables/v04_regression_with_chips_summary_asof_safe.csv",
    },
    {
        "claim_area": "institutional_flow_interactions",
        "artifact_type": "table",
        "legacy": "results/tables/v04_interaction_model_summary.csv",
        "corrected": "results/tables/v04_interaction_model_summary_asof_safe.csv",
    },
    {
        "claim_area": "strategy_group_comparison",
        "artifact_type": "table",
        "legacy": "results/tables/v04_strategy_group_comparison.csv",
        "corrected": None,
        "not_regenerated_reason": "legacy strategy headline is invalidated; no corrected strategy comparison table has been regenerated yet",
    },
    {
        "claim_area": "event_study_caar",
        "artifact_type": "figure",
        "legacy": "results/figures/caar_attention_z2.png",
        "corrected": "results/figures/caar_attention_z2_asof_safe.png",
    },
    {
        "claim_area": "attention_ic",
        "artifact_type": "figure",
        "legacy": "results/figures/ic_decay.png",
        "corrected": None,
        "not_regenerated_reason": "legacy IC figure is invalidated; no corrected IC figure has been regenerated yet",
    },
    {
        "claim_area": "double_sort",
        "artifact_type": "figure",
        "legacy": "results/figures/v03_double_sort_heatmap_4w.png",
        "corrected": "results/figures/v03_double_sort_heatmap_4w_asof_safe.png",
    },
    {
        "claim_area": "residual_attention_ic",
        "artifact_type": "figure",
        "legacy": "results/figures/v03_residual_ic_decay.png",
        "corrected": None,
        "not_regenerated_reason": "legacy residual-IC figure is invalidated; no corrected residual-IC figure has been regenerated yet",
    },
    {
        "claim_area": "institutional_flow_correlation",
        "artifact_type": "figure",
        "legacy": "results/figures/v04_attention_chip_correlation_heatmap.png",
        "corrected": None,
        "not_regenerated_reason": "legacy chip-correlation figure is invalidated; no corrected figure has been regenerated yet",
    },
    {
        "claim_area": "strategy_group_cumulative_return",
        "artifact_type": "figure",
        "legacy": "results/figures/v04_strategy_group_cumulative_return.png",
        "corrected": None,
        "not_regenerated_reason": "legacy strategy figure is invalidated; no corrected cumulative-return figure has been regenerated yet",
    },
    {
        "claim_area": "strategy_group_forward_return",
        "artifact_type": "figure",
        "legacy": "results/figures/v04_strategy_group_forward_return.png",
        "corrected": None,
        "not_regenerated_reason": "legacy strategy figure is invalidated; no corrected forward-return figure has been regenerated yet",
    },
    {
        "claim_area": "triple_sort",
        "artifact_type": "figure",
        "legacy": "results/figures/v04_triple_sort_winner_group_heatmap.png",
        "corrected": "results/figures/v04_triple_sort_winner_group_heatmap_asof_safe.png",
    },
]


def _read_table(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def is_legacy_evidence_candidate(path: Path) -> bool:
    rel = _rel(path)
    if rel in GENERATED_ARTIFACTS or rel in NON_EVIDENCE_ARTIFACTS:
        return False
    if "_asof_safe" in path.stem:
        return False
    return True


def discover_present_legacy_artifacts() -> set[str]:
    present = set()
    for base, pattern in [(TABLES_DIR, "*.csv"), (ROOT / "results" / "figures", "*.png")]:
        if not base.exists():
            continue
        for path in base.glob(pattern):
            rel = _rel(path)
            if not is_legacy_evidence_candidate(path):
                continue
            present.add(rel)
    return present


def assert_legacy_inventory_complete() -> None:
    inventoried = {spec["legacy"] for spec in LEGACY_EVIDENCE}
    missing = sorted(discover_present_legacy_artifacts() - inventoried)
    if missing:
        raise RuntimeError(
            "Legacy evidence inventory is missing present artifact(s): "
            + ", ".join(missing)
        )


def legacy_provenance_rows() -> list[dict]:
    assert_legacy_inventory_complete()
    rows = []
    for spec in LEGACY_EVIDENCE:
        legacy_path = ROOT / spec["legacy"]
        corrected_rel = spec.get("corrected")
        corrected_path = ROOT / corrected_rel if corrected_rel else None
        if corrected_path is None:
            corrected_status = "not_regenerated"
            headline_status = "blocked_not_regenerated"
        elif corrected_path.exists():
            corrected_status = "present"
            headline_status = "corrected_counterpart_available"
        else:
            corrected_status = "missing"
            headline_status = "blocked_corrected_counterpart_missing"

        rows.append({
            "claim_area": spec["claim_area"],
            "artifact_type": spec["artifact_type"],
            "legacy_artifact": spec["legacy"],
            "legacy_status": "superseded_invalidated_by_weekly_availability_bias",
            "legacy_present": legacy_path.exists(),
            "legacy_sha256": file_sha256(legacy_path),
            "corrected_artifact": corrected_rel if corrected_rel else "not_regenerated",
            "corrected_status": corrected_status,
            "corrected_sha256": file_sha256(corrected_path) if corrected_path else None,
            "not_regenerated_reason": spec.get("not_regenerated_reason", ""),
            "headline_evidence_status": headline_status,
        })
    return rows


def compare_pair(spec: dict) -> list[dict]:
    legacy_path = TABLES_DIR / spec["legacy"]
    corrected_path = TABLES_DIR / spec["corrected"]
    legacy = _read_table(legacy_path)
    corrected = _read_table(corrected_path)
    if legacy is None or corrected is None:
        return [{
            "comparison": spec["name"],
            "status": "blocked_missing_table",
            "legacy_table": spec["legacy"],
            "corrected_table": spec["corrected"],
            "reason": "corrected table missing" if corrected is None else "legacy table missing",
        }]

    keys = spec["keys"]
    configured_metrics = spec["metrics"]
    rows = []

    missing_legacy_keys = [c for c in keys if c not in legacy.columns]
    missing_corrected_keys = [c for c in keys if c not in corrected.columns]
    missing_legacy_metrics = [c for c in configured_metrics if c not in legacy.columns]
    missing_corrected_metrics = [c for c in configured_metrics if c not in corrected.columns]

    def add_missing_column_rows(side: str, role: str, columns: list[str]) -> None:
        for column in columns:
            row = {
                "comparison": spec["name"],
                "status": f"blocked_missing_{side}_{role}",
                "legacy_table": spec["legacy"],
                "corrected_table": spec["corrected"],
                "missing_column": column,
                "reason": f"{side} table is missing required {role} column: {column}",
            }
            if role == "metric":
                row["metric"] = column
            rows.append(row)

    add_missing_column_rows("legacy", "key", missing_legacy_keys)
    add_missing_column_rows("corrected", "key", missing_corrected_keys)
    if missing_legacy_keys or missing_corrected_keys:
        return rows

    add_missing_column_rows("legacy", "metric", missing_legacy_metrics)
    add_missing_column_rows("corrected", "metric", missing_corrected_metrics)
    metrics = [m for m in configured_metrics if m in legacy.columns and m in corrected.columns]
    if not metrics:
        rows.append({
            "comparison": spec["name"],
            "status": "blocked_no_common_metrics",
            "legacy_table": spec["legacy"],
            "corrected_table": spec["corrected"],
            "reason": "No configured metrics are present in both tables.",
        })
        return rows

    merged = legacy[keys + metrics].merge(
        corrected[keys + metrics],
        on=keys,
        how="outer",
        suffixes=("_legacy", "_corrected"),
        indicator=True,
    )
    if merged.empty:
        rows.append({
            "comparison": spec["name"],
            "status": "blocked_no_common_keys",
            "legacy_table": spec["legacy"],
            "corrected_table": spec["corrected"],
        })
        return rows

    for _, row in merged.iterrows():
        merge_status = row["_merge"]
        if merge_status == "left_only":
            status = "blocked_missing_corrected_key"
            reason = "Corrected table is missing a key present in the legacy table."
        elif merge_status == "right_only":
            status = "blocked_missing_legacy_key"
            reason = "Legacy table is missing a key present in the corrected table."
        else:
            status = "compared"
            reason = ""

        base = {"comparison": spec["name"], "status": status}
        for key in keys:
            base[key] = row[key]
        for metric in metrics:
            legacy_value = row[f"{metric}_legacy"]
            corrected_value = row[f"{metric}_corrected"]
            out = base.copy()
            out.update({
                "metric": metric,
                "legacy_value": legacy_value,
                "corrected_value": corrected_value,
            })
            if reason:
                out["reason"] = reason
            if (
                pd.api.types.is_number(legacy_value)
                and pd.api.types.is_number(corrected_value)
                and pd.notna(legacy_value)
                and pd.notna(corrected_value)
            ):
                out["delta_corrected_minus_legacy"] = corrected_value - legacy_value
            rows.append(out)
    return rows


def panel_provenance() -> list[dict]:
    rows = []
    for name, path in {
        "legacy_v03_panel": PROCESSED_DIR / "attention_weekly_panel_v03.csv",
        "corrected_v03_panel": PROCESSED_DIR / "attention_weekly_panel_v03_asof_safe.csv",
        "legacy_v04_panel": PROCESSED_DIR / "attention_weekly_panel_v04.csv",
        "corrected_v04_panel": PROCESSED_DIR / "attention_weekly_panel_v04_asof_safe.csv",
    }.items():
        if not path.exists():
            rows.append({"artifact": name, "path": str(path.relative_to(ROOT)), "status": "missing"})
            continue
        df = pd.read_csv(path)
        date_col = "week" if "week" in df.columns else None
        rows.append({
            "artifact": name,
            "path": str(path.relative_to(ROOT)),
            "status": "present",
            "n_rows": len(df),
            "n_stocks": df["stock_id"].nunique() if "stock_id" in df.columns else None,
            "sample_start": df[date_col].min() if date_col else None,
            "sample_end": df[date_col].max() if date_col else None,
        })
    return rows


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    comparison_rows = []
    for spec in COMPARISONS:
        comparison_rows.extend(compare_pair(spec))
    pd.DataFrame(comparison_rows).to_csv(
        TABLES_DIR / "asof_safe_legacy_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )

    pd.DataFrame(legacy_provenance_rows()).to_csv(
        TABLES_DIR / "legacy_results_provenance.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(panel_provenance()).to_csv(
        TABLES_DIR / "panel_provenance_asof_safe.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print("Saved asof_safe_legacy_comparison.csv, legacy_results_provenance.csv, and panel_provenance_asof_safe.csv")


if __name__ == "__main__":
    main()
