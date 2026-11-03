"""Descriptive paired pre/post study for target-service CPU and API-facing metrics.

This is not Wave v3: RE2-OB does not provide the current v3 contract's explicit
completed/failed request counts and mean latency in its metrics table.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import pandas as pd

from adapter import find_cases

PHASE_SECONDS = 600


def median_between(frame: pd.DataFrame, column: str, start: int, end: int):
    if column not in frame.columns:
        return None
    values = frame.loc[(frame.time >= start) & (frame.time < end), column].dropna()
    return float(values.median()) if not values.empty else None


def delta(before, after):
    if before is None or after is None:
        return None
    return after - before


def pct_change(before, after):
    if before is None or after is None or before == 0:
        return None
    return 100.0 * (after - before) / abs(before)


def analyze_case(case_dir: Path) -> dict:
    from adapter import parse_case_name, read_metrics

    identity = parse_case_name(case_dir.name)
    frame = read_metrics(case_dir)
    inject = int((case_dir / "inject_time.txt").read_text(encoding="utf-8-sig").strip())
    pre_start, pre_end = inject - PHASE_SECONDS, inject
    post_start, post_end = inject, inject + PHASE_SECONDS
    target_cpu_col = f"{identity['service']}_cpu"
    api_candidates = {
        "frontend_latency_p50_candidate": "frontend_latency-50",
        "frontend_latency_p90_candidate": "frontend_latency-90",
        "frontend_workload_candidate": "frontend-external_workload",
        "frontend_error_candidate": "frontend-external_error",
    }
    result = {**identity, "inject_time_unix_seconds": inject,
              "phase_seconds": PHASE_SECONDS, "pre_rows": int(((frame.time >= pre_start) & (frame.time < pre_end)).sum()),
              "post_rows": int(((frame.time >= post_start) & (frame.time < post_end)).sum()),
              "cpu_metric_name_candidate": target_cpu_col}
    before = {}
    after = {}
    columns = {"target_service_cpu_candidate": target_cpu_col, **api_candidates}
    for output_key, column in columns.items():
        before[output_key] = median_between(frame, column, pre_start, pre_end)
        after[output_key] = median_between(frame, column, post_start, post_end)
        result[f"{output_key}_pre_median"] = before[output_key]
        result[f"{output_key}_post_median"] = after[output_key]
        result[f"{output_key}_delta"] = delta(before[output_key], after[output_key])
        result[f"{output_key}_change_percent"] = pct_change(before[output_key], after[output_key])
    result["scope_note"] = (
        "Descriptive episode association only. Names suggest signals but units/definitions are not confirmed. "
        "Latency p50/p90 are not v3 mean latency; workload/error columns are not proven request counts."
    )
    return result


def summarize(rows: list[dict]) -> dict:
    grouped = {}
    for fault in ("cpu", "delay"):
        subset = [row for row in rows if row["fault"] == fault]
        stats = {}
        for key in ("target_service_cpu_candidate_delta",
                    "frontend_latency_p90_candidate_delta",
                    "frontend_workload_candidate_delta", "frontend_error_candidate_delta"):
            values = [row[key] for row in subset if row.get(key) is not None and math.isfinite(row[key])]
            stats[key] = {"n_cases": len(values), "median_case_delta": float(pd.Series(values).median()) if values else None}
        grouped[fault] = {"case_count": len(subset), "median_deltas": stats}
    return {
        "study": "RCAEval RE2-OB CPU/API-facing event study",
        "phase_definition": "600 seconds immediately before injection vs 600 seconds from injection onward",
        "case_count": len(rows), "groups": grouped,
        "wave_v3_executed": False,
        "reason_wave_v3_not_executed": "No explicit completed and failed request counts plus mean latency are present in the metric schema; documented p50/p90 fields cannot substitute for mean latency, and workload/error semantics require source confirmation.",
        "interpretation": "Exploratory descriptive association by independent case; fault labels identify injected causes and are not API impact labels. No causal or detector-performance claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("research/reports/rcaeval_re2ob/generated"))
    args = parser.parse_args()
    cases = find_cases(args.dataset_root)
    if len(cases) != 30:
        raise RuntimeError(f"Expected all 30 CPU/delay cases; found {len(cases)}")
    rows = [analyze_case(path) for path in cases]
    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "event_study_by_case.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = summarize(rows)
    report["case_results_csv"] = csv_path.name
    (args.out / "event_study_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "cases": report["case_count"], "wave_v3_executed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
