"""Local readers and audit helpers for RCAEval RE2-OB cases.

The adapter does not infer metric semantics. Wave input mapping must be
specified only after the inventory and source documentation have been checked.
"""
from __future__ import annotations

import json
import re
import csv
from collections import Counter
from pathlib import Path

import pandas as pd

CASE_RE = re.compile(r"^re2ob_(?P<service>.+)_(?P<fault>cpu|delay)_(?P<repetition>\d+)$")
SIGNAL_PATTERNS = {
    "cpu_name_candidates": re.compile(r"cpu", re.I),
    "latency_name_candidates": re.compile(r"latency|duration|rrt", re.I),
    "request_name_candidates": re.compile(r"request|throughput|goodput", re.I),
    "error_name_candidates": re.compile(r"error|fail|status", re.I),
}


def parse_case_name(name: str) -> dict | None:
    match = CASE_RE.fullmatch(name)
    if not match:
        return None
    return {"case": name, "service": match["service"], "fault": match["fault"],
            "repetition": int(match["repetition"])}


def find_cases(dataset_root: Path) -> list[Path]:
    """Find data case directories while excluding the RCAEval source tree."""
    if not dataset_root.exists():
        return []
    found = []
    for path in dataset_root.rglob("re2ob_*"):
        if not path.is_dir() or parse_case_name(path.name) is None:
            continue
        has_metrics = (path / "metrics.parquet").is_file() or (path / "metrics.json").is_file()
        if has_metrics and (path / "inject_time.txt").is_file():
            found.append(path)
    return sorted(found)


def read_metrics(case_dir: Path) -> pd.DataFrame:
    """Read lossless union timestamps; missing values stay null, no fill/resample."""
    parquet = case_dir / "metrics.parquet"
    if parquet.is_file():
        frame = pd.read_parquet(parquet)
    else:
        json_path = case_dir / "metrics.json"
        if not json_path.is_file():
            raise FileNotFoundError(f"no metrics.parquet or metrics.json in {case_dir}")
        raw = json.loads(json_path.read_text(encoding="utf-8-sig"))
        timestamps = sorted({int(point[0]) for points in raw.values() for point in points})
        by_time = {ts: i for i, ts in enumerate(timestamps)}
        frame = pd.DataFrame(index=range(len(timestamps)))
        frame.insert(0, "time", timestamps)
        for metric, points in raw.items():
            values = [float("nan")] * len(timestamps)
            for timestamp, value in points:
                if value is not None:
                    values[by_time[int(timestamp)]] = float(value)
            frame[metric] = values
    if "time" not in frame.columns:
        raise ValueError(f"metrics table has no time column: {case_dir}")
    frame = frame.sort_values("time", kind="stable").reset_index(drop=True)
    times = frame["time"].astype("int64")
    if times.duplicated().any():
        raise ValueError(f"duplicate union timestamps in {case_dir}")
    frame["time"] = times
    return frame


def trace_metadata(case_dir: Path) -> dict:
    parquet = case_dir / "traces.parquet"
    csv_path = case_dir / "traces.csv"
    if parquet.is_file():
        import pyarrow.parquet as pq
        metadata = pq.ParquetFile(parquet).metadata
        schema = list(pq.ParquetFile(parquet).schema.names)
        return {"path": str(parquet), "rows": metadata.num_rows, "columns": schema}
    if csv_path.is_file():
        with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            columns = next(csv.reader(stream), [])
        with csv_path.open("rb") as stream:
            rows = max(sum(1 for _ in stream) - 1, 0)
        return {"path": str(csv_path), "rows": rows, "columns": columns}
    return {"path": None, "rows": 0, "columns": []}


def inventory_case(case_dir: Path) -> dict:
    identity = parse_case_name(case_dir.name)
    if identity is None:
        raise ValueError(f"not an RE2-OB cpu/delay case: {case_dir.name}")
    frame = read_metrics(case_dir)
    inject_time = int((case_dir / "inject_time.txt").read_text(encoding="utf-8-sig").strip())
    times = frame["time"].to_numpy()
    if not len(times):
        raise ValueError(f"empty metrics timeline: {case_dir}")
    diffs = [int(b - a) for a, b in zip(times, times[1:]) if b > a]
    metrics = [c for c in frame.columns if c != "time"]
    candidate_names = {key: [name for name in metrics if pattern.search(name)]
                       for key, pattern in SIGNAL_PATTERNS.items()}
    counts = Counter(diffs)
    return {
        **identity, "case_path": str(case_dir), "inject_time_unix_seconds": inject_time,
        "time_start_unix_seconds": int(times[0]), "time_end_unix_seconds": int(times[-1]),
        "metric_column_count": len(metrics), "metric_rows": len(frame),
        "rows_before_injection": int((frame["time"] < inject_time).sum()),
        "rows_at_or_after_injection": int((frame["time"] >= inject_time).sum()),
        "interval_seconds_mode": counts.most_common(1)[0][0] if counts else None,
        "interval_seconds_counts": dict(sorted(counts.items())),
        "metric_names": metrics, "name_only_candidates_not_semantic_mappings": candidate_names,
        "trace": trace_metadata(case_dir),
        "scope_note": "Fault/service are case labels, not an API impact label. Metric names are not unit or temporality proof.",
    }


def summarize_inventory(dataset_root: Path) -> dict:
    cases = find_cases(dataset_root)
    details = [inventory_case(path) for path in cases]
    groups = Counter((case["fault"], case["service"]) for case in details)
    return {
        "dataset": "RCAEval RE2-OB", "dataset_root": str(dataset_root),
        "case_count": len(details), "case_group_counts": {
            f"{fault}:{service}": count for (fault, service), count in sorted(groups.items())},
        "cases": details,
        "metric_semantics_confirmed": False,
        "recommendation": ("inventory_only_no_case_data_found" if not details else
                           "review_units_temporality_and_candidate_names_before_wave_mapping"),
    }
