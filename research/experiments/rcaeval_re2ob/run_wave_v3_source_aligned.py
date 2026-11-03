"""Run unchanged Wave v3 on the API-entry trace operation identified in RE2-OB.

RCAEval's toolkit groups spans by service/operation, converts Jaeger duration
from microseconds to milliseconds, and counts explicit non-OK/non-HTTP-success
statuses as errors. In RE2-OB, the `frontend` operation on `frontendservice` is
the observed root/API-entry operation. Its statusCode is absent, so v3 must
leave failed counts missing. CPU remains an adjacent raw candidate because its
unit is not documented as cores.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "research" / "src"))
from aim_wave.v3 import MODEL_ID, REFERENCES, derive  # noqa: E402

if __package__:
    from .adapter import find_cases, parse_case_name
else:
    from adapter import find_cases, parse_case_name

WINDOW_SECONDS = 60
DEFAULT_API_SERVICE = "frontendservice"
DEFAULT_API_OPERATION = "frontend"
RCA_EVAL_SOURCE = "RCAEval/agent/toolkit.py:267-281,410-445"


def _epoch_seconds(series: pd.Series) -> pd.Series:
    """Apply RCAEval toolkit's magnitude-based epoch unit conversion."""
    values = pd.to_numeric(series, errors="coerce")
    sample = values.dropna()
    if sample.empty:
        return values
    magnitude = float(sample.iloc[0])
    for threshold, scale in ((1e17, 1e9), (1e14, 1e6), (1e11, 1e3)):
        if magnitude > threshold:
            return values / scale
    return values


def _error_status(status: pd.Series) -> int:
    known = pd.to_numeric(status, errors="coerce").dropna()
    if known.empty:
        return 0
    success = known.eq(0) | known.between(200, 399)
    return int((~success).sum())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def process_case(case_dir: Path, api_service: str = DEFAULT_API_SERVICE,
                 api_operation: str = DEFAULT_API_OPERATION) -> list[dict]:
    identity = parse_case_name(case_dir.name)
    metrics = pd.read_parquet(case_dir / "metrics.parquet")
    traces = pd.read_parquet(case_dir / "traces.parquet")
    inject = int((case_dir / "inject_time.txt").read_text(encoding="utf-8-sig").strip())
    metric_start, metric_end = int(metrics.time.min()), int(metrics.time.max())
    cpu_col = f"{identity['service']}_cpu"

    traces = traces.loc[traces.serviceName.eq(api_service) & traces.operationName.eq(api_operation)].copy()
    traces["epoch_seconds"] = _epoch_seconds(traces.startTime).astype("float64")
    traces = traces.dropna(subset=["epoch_seconds"])
    traces["duration_microseconds"] = pd.to_numeric(traces.duration, errors="coerce")

    # Select one observed API-entry operation. The source toolkit groups by both
    # service and operation; aggregating every frontendservice operation would
    # count nested RPC spans as external API requests.
    rows = []
    count = math.ceil((metric_end + 1 - metric_start) / WINDOW_SECONDS)
    for index in range(count):
        start = metric_start + index * WINDOW_SECONDS
        end = min(start + WINDOW_SECONDS, metric_end + 1)
        seconds = traces.loc[(traces.epoch_seconds >= start) & (traces.epoch_seconds < end)]
        metric_window = metrics.loc[(metrics.time >= start) & (metrics.time < end)]
        request_total = int(len(seconds))
        status_known = int(pd.to_numeric(seconds.statusCode, errors="coerce").notna().sum())
        failures = _error_status(seconds.statusCode) if status_known else (0 if request_total == 0 else None)
        mean_latency_seconds = (
            float(seconds.duration_microseconds.mean() / 1_000_000)
            if not seconds.duration_microseconds.dropna().empty else None
        )
        cpu_raw = (
            float(metric_window[cpu_col].mean())
            if cpu_col in metric_window and not metric_window[cpu_col].dropna().empty else None
        )
        raw = {
            "service": api_service, "window_index": index,
            "start_utc": start, "end_utc": end,
            "duration_seconds": float(end - start),
            "completed": request_total, "failed": failures,
            "mean_latency_seconds": mean_latency_seconds,
            "cpu_cores": None, "counter_reset": False,
        }
        wave = derive(raw, "rcaeval_re2ob_traces_via_official_toolkit_semantics", REFERENCES)
        rows.append({
            "case": case_dir.name, "fault": identity["fault"],
            "injected_service": identity["service"], "api_service": api_service,
            "api_operation": api_operation,
            "window_index": index, "window_start_unix_seconds": start,
            "window_end_unix_seconds": end, "window_duration_seconds": end - start,
            "injection_active": start >= inject, "trace_request_spans": request_total,
            "trace_status_known": status_known,
            "trace_status_coverage": status_known / request_total if request_total else None,
            "trace_errors_by_rcaeval_rule": failures,
            "mean_span_duration_seconds": mean_latency_seconds,
            "cpu_metric_name_candidate": cpu_col, "cpu_metric_raw_mean_candidate": cpu_raw,
            "cpu_cores_input": None,
            "model_id": wave["model_id"], "status": wave["status"], "reason": wave["reason"],
            "S": wave["S"], "goodput_per_second": wave["goodput_per_second"],
            "P_raw": wave["P_raw"], "P": wave["P"], "Q": wave["Q"], "D": wave["D"],
            "theta": wave["theta"],
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--api-service", default=DEFAULT_API_SERVICE)
    parser.add_argument("--api-operation", default=DEFAULT_API_OPERATION)
    parser.add_argument("--out", type=Path, default=Path("research/reports/rcaeval_re2ob/generated"))
    args = parser.parse_args()
    cases = find_cases(args.dataset_root)
    if len(cases) != 30:
        raise RuntimeError(f"Expected 30 RE2-OB CPU/delay cases; found {len(cases)}")
    rows = [row for case in cases for row in process_case(case, args.api_service, args.api_operation)]
    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "wave_v3_source_aligned_windows.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    hashes = {
        str(path.relative_to(args.dataset_root)): _sha256(path)
        for case in cases for path in (case / "metrics.parquet", case / "traces.parquet", case / "inject_time.txt")
    }
    status_counts = pd.Series([row["status"] for row in rows]).value_counts().to_dict()
    reason_counts = pd.Series([row["reason"] or "none" for row in rows]).value_counts().to_dict()
    report = {
        "experiment": "rcaeval-re2ob-wave-v3-source-aligned-001",
        "model_id": MODEL_ID, "references": REFERENCES,
        "dataset_case_count": len(cases), "api_service": args.api_service,
        "api_operation": args.api_operation,
        "window_seconds": WINDOW_SECONDS, "window_count": len(rows),
        "status_counts": status_counts,
        "reason_counts": reason_counts,
        "valid_v3_windows": sum(row["status"] == "ok" for row in rows),
        "partial_or_missing_windows": sum(row["status"] != "ok" for row in rows),
        "api_span_count": sum(row["trace_request_spans"] for row in rows),
        "api_spans_with_status_code": sum(row["trace_status_known"] for row in rows),
        "api_windows_with_duration": sum(row["mean_span_duration_seconds"] is not None for row in rows),
        "cpu_cores_populated": sum(row["cpu_cores_input"] is not None for row in rows),
        "computed_v3_indices": False,
        "cpu_candidate_preserved_separately": True,
        "source_semantics": {
            "reference": RCA_EVAL_SOURCE,
            "requests": "Spans for the selected service/operation in the time window, matching the toolkit's service-operation grouping. The selected operation is observed as parentless in all downloaded cases.",
            "duration": "Source toolkit states Jaeger duration is microseconds; mean converted to seconds for v3.",
            "errors": "Source toolkit treats gRPC status 0 and HTTP 200-399 as success; other explicit statuses count as errors. Missing status rows do not count as errors, as in the toolkit's sum behavior.",
            "caveat": "The selected frontend API-entry operation has no statusCode on all observed spans, so failed counts remain missing and Wave does not compute P/Q/D. Aggregating every frontendservice operation instead inflates request volume with nested RPC spans and saturates P at the fixed reference; that aggregate is not used as an API input.",
            "cpu": "CPU metric names identify candidate series; its unit is not confirmed as CPU cores, so it is not passed to cpu_cores. The raw metric mean is retained beside v3 output.",
        },
        "interpretation": "The unchanged v3 was invoked on API-entry operation windows. It emitted only missing/no-traffic states because failed counts are unavailable; no P/Q/D indices were computed. CPU remains an external candidate covariate; do not interpret associations as causal or detector performance.",
        "source_sha256": hashes, "window_results_csv": csv_path.name,
    }
    (args.out / "wave_v3_source_aligned_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(cases), "windows": len(rows), "status_counts": status_counts,
                      "valid_v3_windows": report["valid_v3_windows"],
                      "api_spans_with_status_code": report["api_spans_with_status_code"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
