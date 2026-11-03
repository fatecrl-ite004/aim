"""Schema and event readers for AD-microservice-app; metric names remain candidates."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

LABEL_COLUMNS = ("anomaly_load", "anomaly_fis", "anomaly")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_day(day_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    day = day_dir.name
    metric_path = day_dir / f"{day}_metrics.csv"
    actions_path = day_dir / f"{day}_FIS_Experiment_Actions.csv"
    if not metric_path.is_file() or not actions_path.is_file():
        raise FileNotFoundError(f"Expected {metric_path.name} and {actions_path.name} in {day_dir}")
    metrics = pd.read_csv(metric_path, low_memory=False)
    actions = pd.read_csv(actions_path, low_memory=False)
    if "time" not in metrics:
        raise ValueError(f"metrics file has no time column: {metric_path}")
    metrics["time"] = pd.to_datetime(metrics["time"], utc=True, errors="coerce")
    if metrics.time.isna().any():
        raise ValueError(f"unparseable metric timestamps in {metric_path}")
    actions["start_utc"] = pd.to_datetime(actions["Action Start Time"], utc=True, errors="coerce")
    actions["end_utc"] = pd.to_datetime(actions["Action End Time"], utc=True, errors="coerce")
    return metrics, actions


def parity_audit(metrics: pd.DataFrame) -> dict:
    services = sorted({c.removesuffix("_req_rate") for c in metrics if c.endswith("_req_rate")})
    comparisons = {"req_rate_equals_req_ok": [], "avg_rt_equals_avg_ok_rt": []}
    for service in services:
        for suffix_a, suffix_b, key in (
            ("_req_rate", "_req_ok", "req_rate_equals_req_ok"),
            ("_avg_rt", "_avg_ok_rt", "avg_rt_equals_avg_ok_rt"),
        ):
            left, right = f"{service}{suffix_a}", f"{service}{suffix_b}"
            if left in metrics and right in metrics:
                equal = metrics[left].eq(metrics[right]) | (metrics[left].isna() & metrics[right].isna())
                comparisons[key].append({"service": service, "rows_equal": int(equal.sum()),
                                         "rows_compared": len(metrics), "all_equal": bool(equal.all())})
    return {"services": services, **comparisons,
            "failed_candidate_nonzero_rows": {s: int((metrics[f"{s}_req_ko"].fillna(0) != 0).sum())
                                               for s in services if f"{s}_req_ko" in metrics}}


def action_records(actions: pd.DataFrame) -> list[dict]:
    records = []
    for idx, row in actions.iterrows():
        target = str(row.get("Target", ""))
        service = target.split("||", 1)[1] if "||" in target else None
        records.append({
            "source_row": int(idx), "experiment_id": str(row.get("Experiment ID", "")),
            "action_name": str(row.get("Action Name", "")),
            "target_type": str(row.get("Target Type", "")), "target": target,
            "target_service_candidate": service,
            "start_utc": row["start_utc"].isoformat() if pd.notna(row["start_utc"]) else None,
            "end_utc": row["end_utc"].isoformat() if pd.notna(row["end_utc"]) else None,
        })
    for record in records:
        start, end = record["start_utc"], record["end_utc"]
        overlaps = []
        if start and end:
            s, e = pd.Timestamp(start), pd.Timestamp(end)
            for other in records:
                if other is record or not other["start_utc"] or not other["end_utc"]:
                    continue
                os_, oe = pd.Timestamp(other["start_utc"]), pd.Timestamp(other["end_utc"])
                if max(s, os_) < min(e, oe):
                    overlaps.append(other["experiment_id"])
        record["overlapping_experiment_ids"] = sorted(set(overlaps))
    return records


def inventory_day(day_dir: Path) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    metrics, actions = load_day(day_dir)
    diff_s = metrics.time.diff().dt.total_seconds().dropna()
    labels = [name for name in LABEL_COLUMNS if name in metrics]
    metric_cols = [c for c in metrics if c != "time"]
    records = action_records(actions)
    cpu = [r for r in records if "cpu" in r["action_name"].lower()]
    summary = {
        "dataset_day": day_dir.name, "metric_rows": len(metrics), "metric_columns": len(metric_cols),
        "time_start_utc": metrics.time.min().isoformat(), "time_end_utc": metrics.time.max().isoformat(),
        "duplicate_timestamps": int(metrics.time.duplicated().sum()),
        "timestamp_interval_seconds_counts": {str(k): int(v) for k, v in diff_s.value_counts().sort_index().items()},
        "missing_cells_by_column": {c: int(metrics[c].isna().sum()) for c in metric_cols if metrics[c].isna().any()},
        "entity_column_counts": {
            "node": sum(c.startswith("node_") for c in metric_cols),
            "pod": sum(c.startswith("pod_") for c in metric_cols),
            "service": sum(not c.startswith(("node_", "pod_")) and c not in labels for c in metric_cols),
            "ground_truth_labels": labels,
        },
        "action_count": len(records), "action_count_by_name": actions["Action Name"].value_counts(dropna=False).to_dict(),
        "missing_action_end_count": int(actions["end_utc"].isna().sum()),
        "overlapping_action_count": sum(bool(r["overlapping_experiment_ids"]) for r in records),
        "cpu_action_count": len(cpu), "cpu_action_overlap_count": sum(bool(r["overlapping_experiment_ids"]) for r in cpu),
        "cpu_actions": cpu, "service_api_parity_audit": parity_audit(metrics),
        "cpu_metric_name_candidates": [c for c in metric_cols if c.startswith(("pod_cpu_utilization|Average|", "node_cpu_usage_total|Average|"))],
        "api_metric_name_candidates": [c for c in metric_cols if any(tag in c for tag in ("_req_rate", "_req_ok", "_req_ko", "_avg_rt", "_avg_ok_rt"))],
        "semantics_note": "Metric names and FIS/anomaly labels are candidates/labels only; units and request semantics are not asserted.",
    }
    return summary, metrics, actions


def event_study(summary: dict, metrics: pd.DataFrame) -> list[dict]:
    results = []
    for action in summary["cpu_actions"]:
        if not action["start_utc"] or not action["end_utc"]:
            continue
        start, end = pd.Timestamp(action["start_utc"]), pd.Timestamp(action["end_utc"])
        service = action["target_service_candidate"]
        if action["target_type"].lower() == "pod" and service:
            cpu_col = f"pod_cpu_utilization|Average|{service}"
        elif action["target_type"].lower() == "node":
            cpu_col = f"node_cpu_usage_total|Average|{action['target']}"
        else:
            cpu_col = None
        # Each phase is timestamp-matched; labels are deliberately not used as API impact.
        phases = {"pre": (start - pd.Timedelta(minutes=5), start),
                  "during": (start, end), "post": (end, end + pd.Timedelta(minutes=5))}
        row = {**action, "cpu_metric_candidate": cpu_col,
               "api_service_candidate": "front-end",
               "api_metrics_are_name_candidates_only": True,
               "overlap_excluded_from_clean_estimate": bool(action["overlapping_experiment_ids"])}
        columns = [c for c in (cpu_col, "front-end_req_rate", "front-end_req_ok", "front-end_req_ko",
                               "front-end_avg_rt", "front-end_avg_ok_rt") if c and c in metrics]
        for phase, (lo, hi) in phases.items():
            subset = metrics.loc[(metrics.time >= lo) & (metrics.time < hi), columns]
            row[f"{phase}_sample_count"] = len(subset)
            for col in columns:
                row[f"{phase}_median__{col}"] = float(subset[col].median()) if subset[col].notna().any() else None
        row["interpretation_limit"] = "Descriptive co-occurrence only; no causal claim. API field names are not mapped to Wave inputs."
        results.append(row)
    return results
