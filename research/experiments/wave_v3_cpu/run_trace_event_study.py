"""Compare locked Wave v3 outputs with trace latency around labeled events.

Trace-derived percentiles are evaluation outcomes only. They are not passed to
or used to modify the Wave v3 equations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "research" / "src"))
from aim_wave.v3 import MODEL_ID, REFERENCES  # noqa: E402

PHASES = ("before", "during", "after")
EVENT_TYPES = {"cpu", "delay"}


def episodes(events: list[dict]) -> list[dict]:
    """Group simultaneous same-type/service injections as one episode."""
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for event in events:
        if event["failure_type"] not in EVENT_TYPES:
            continue
        key = (int(event["timestamp"]), int(event["duration"]), event["failure_type"])
        grouped[key].append(event)
    result = []
    for (start, duration, kind), group in sorted(grouped.items()):
        result.append({"episode_id": f"{kind}-{start}", "failure_type": kind,
                       "start": start, "end": start + duration, "duration": duration,
                       "services": sorted({str(e["service"]) for e in group}),
                       "instances": sorted({str(e["cmdb_id"]) for e in group})})
    return result


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile (p in [0,1]); no interpolation or hidden trim."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def summarize(values: list[float], scale: float = 1.0) -> dict:
    return {"n": len(values), "mean": (sum(values) / len(values) / scale if values else None),
            "p50": (percentile(values, .50) / scale if values else None),
            "p95": (percentile(values, .95) / scale if values else None),
            "max": (max(values) / scale if values else None)}


def phase_for(timestamp_seconds: float, event: dict) -> str | None:
    if event["start"] - event["duration"] <= timestamp_seconds < event["start"]:
        return "before"
    if event["start"] <= timestamp_seconds < event["end"]:
        return "during"
    if event["end"] <= timestamp_seconds < event["end"] + event["duration"]:
        return "after"
    return None


def phase_interval(event: dict, phase: str) -> tuple[int, int]:
    if phase == "before":
        return event["start"] - event["duration"], event["start"]
    if phase == "during":
        return event["start"], event["end"]
    return event["end"], event["end"] + event["duration"]


def phase_interventions(event: dict, phase: str, all_events: list[dict]) -> list[dict]:
    start, end = phase_interval(event, phase)
    return [{"timestamp": int(other["timestamp"]), "duration": int(other["duration"]),
             "service": str(other["service"]), "cmdb_id": str(other["cmdb_id"]),
             "failure_type": str(other["failure_type"]),
             "same_episode": (other["failure_type"] == event["failure_type"] and
                              int(other["timestamp"]) == event["start"] and
                              int(other["duration"]) == event["duration"])}
            for other in all_events
            if int(other["timestamp"]) < end and
            int(other["timestamp"]) + int(other["duration"]) > start]


def load_groundtruth(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    keys = ("timestamp", "service", "cmdb_id", "failure_type", "duration")
    if len({len(data.get(k, [])) for k in keys}) != 1:
        raise ValueError(f"inconsistent groundtruth columns: {path}")
    return [{k: data[k][i] for k in keys} for i in range(len(data.get("timestamp", [])))]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class _HashingRaw(io.RawIOBase):
    def __init__(self, source, digest):
        self.source, self.digest = source, digest

    def readable(self):
        return True

    def readinto(self, buffer):
        block = self.source.read(len(buffer))
        self.digest.update(block)
        buffer[:len(block)] = block
        return len(block)


def read_trace_events(trace_path: Path, event_list: list[dict]) -> tuple[dict, dict]:
    """Scan the full CSV once; retain only request spans in event study windows."""
    picked: dict[tuple[str, str], list[float]] = defaultdict(list)
    statuses: dict[tuple[str, str], Counter] = defaultdict(Counter)
    span_types: dict[tuple[str, str], Counter] = defaultdict(Counter)
    audit = {"rows_read": 0, "malformed_or_invalid_rows": 0,
             "selected_target_request_spans": 0, "selected_root_request_spans": 0,
             "selected_target_spans_by_type": {},
             "timestamp_divisor": 1_000_000,
             "timestamp_unit_interpretation": "microseconds, inferred from epoch magnitude and sampling timestamps",
             "min_timestamp_seconds": None, "max_timestamp_seconds": None}
    digest = hashlib.sha256()
    with trace_path.open("rb") as binary:
        raw = _HashingRaw(binary, digest)
        stream = io.TextIOWrapper(io.BufferedReader(raw), encoding="utf-8-sig", newline="")
        reader = csv.DictReader(stream)
        required = {"timestamp", "cmdb_id", "duration", "type", "status_code", "parent_span"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"trace schema missing: {sorted(required - set(reader.fieldnames or []))}")
        for row in reader:
            audit["rows_read"] += 1
            try:
                ts = float(row["timestamp"]) / 1_000_000.0
                duration = float(row["duration"])
                if not math.isfinite(ts) or not math.isfinite(duration) or duration < 0:
                    raise ValueError
            except (TypeError, ValueError):
                audit["malformed_or_invalid_rows"] += 1
                continue
            audit["min_timestamp_seconds"] = ts if audit["min_timestamp_seconds"] is None else min(audit["min_timestamp_seconds"], ts)
            audit["max_timestamp_seconds"] = ts if audit["max_timestamp_seconds"] is None else max(audit["max_timestamp_seconds"], ts)
            is_request = row.get("type") == "request"
            service = row.get("cmdb_id", "")
            is_root = is_request and not row.get("parent_span") and service == "frontend"
            for event in event_list:
                phase = phase_for(ts, event)
                if phase is None:
                    continue
                if service in event["services"]:
                    type_key = (event["episode_id"], f"{phase}:target_type:{row.get('type', '')}")
                    span_types[type_key][row.get("type", "")] += 1
                    if is_request:
                        key = (event["episode_id"], f"{phase}:target_service")
                        picked[key].append(duration)
                        statuses[key][row.get("status_code", "")] += 1
                        audit["selected_target_request_spans"] += 1
                    else:
                        key = (event["episode_id"], f"{phase}:target_span_type:{row.get('type', '')}")
                        picked[key].append(duration)
                if is_root:
                    key = (event["episode_id"], f"{phase}:root_request")
                    picked[key].append(duration)
                    statuses[key][row.get("status_code", "")] += 1
                    audit["selected_root_request_spans"] += 1
        stream.close()
    audit["source_sha256"] = digest.hexdigest()
    audit["selected_target_spans_by_type"] = {
        f"{episode}:{phase}": dict(counts) for (episode, phase), counts in span_types.items()}
    return {"durations_us": picked, "statuses": statuses, "span_types": span_types}, audit


def features_by_episode(csv_path: Path, event_list: list[dict], case_name: str) -> dict:
    """Summarize already-computed v3 rows for faulted instances and phases."""
    fields = ("cpu_cores", "latency_seconds", "throughput_rps", "error_percent", "P", "D")
    values: dict[tuple[str, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    coverage: Counter = Counter()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("case") != case_name:
                continue
            if row.get("instance") not in {i for e in event_list for i in e["instances"]}:
                continue
            try:
                midpoint = (float(row["window_start_epoch_seconds"]) + float(row["window_end_epoch_seconds"])) / 2
            except (TypeError, ValueError):
                continue
            for event in event_list:
                if row.get("instance") not in event["instances"]:
                    continue
                phase = phase_for(midpoint, event)
                if phase is None:
                    continue
                coverage[(event["episode_id"], phase, row.get("status", ""), row.get("reason", ""))] += 1
                if row.get("status") != "ok":
                    continue
                for field in fields:
                    if row.get(field, "") == "":
                        continue
                    try:
                        v = float(row[field])
                    except ValueError:
                        continue
                    if math.isfinite(v):
                        values[(event["episode_id"], phase, field)]["values"].append(v)
    summary = {}
    for event in event_list:
        block = {}
        for phase in PHASES:
            block[phase] = {field: summarize(values[(event["episode_id"], phase, field)]["values"],
                                                   1.0 if field not in ("latency_seconds",) else 1.0)
                            for field in fields}
            block[phase]["window_status_counts"] = {
                status_key: count for (eid, ph, status, reason), count in coverage.items()
                if eid == event["episode_id"] and ph == phase
                for status_key in [f"{status}:{reason or 'none'}"]}
        summary[event["episode_id"]] = block
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--features-csv", type=Path,
                        default=Path(__file__).resolve().parents[2] / "reports" / "wave_v3_cpu" / "generated" / "wave_v3_cpu_windows.csv")
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parents[2] / "reports" / "wave_v3_cpu" / "generated" / "trace_event_study.json")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    episodes_by_case = {}
    feature_summary = {}
    traces = {}
    audits = {}
    source_hashes = {}
    for case_name in ("Case-1", "Case-2"):
        case_dir = args.dataset_root / case_name / case_name
        if not case_dir.is_dir():
            raise FileNotFoundError(case_dir)
        all_events = load_groundtruth(case_dir / "groundtruth" / "groundtruth.json")
        evts = episodes(all_events)
        episodes_by_case[case_name] = evts
        feature_summary[case_name] = features_by_episode(args.features_csv, evts, case_name)
        trace_path = case_dir / "trace" / "trace.csv"
        print(f"Scanning {case_name} trace: {trace_path.stat().st_size} bytes", flush=True)
        scan, audits[case_name] = read_trace_events(trace_path, evts)
        source_hashes[f"{case_name}/trace.csv"] = audits[case_name]["source_sha256"]
        traces[case_name] = {
            event["episode_id"]: {
                phase: {
                    **{kind: {
                        **summarize(scan["durations_us"].get((event["episode_id"], f"{phase}:{kind}"), []), 1000.0),
                        "status_code_counts": dict(scan["statuses"].get((event["episode_id"], f"{phase}:{kind}"), {}))}
                       for kind in ("target_service", "root_request")},
                    "other_target_span_types": {
                        span_type: summarize(scan["durations_us"].get(
                            (event["episode_id"], f"{phase}:target_span_type:{span_type}"), []), 1000.0)
                        for eid, phase_type in scan["span_types"]
                        for phase_name, _, span_type in [phase_type.split(":", 2)]
                        if eid == event["episode_id"] and phase_name == phase and span_type != "request"
                    }
                } for phase in PHASES
            } for event in evts
        }
        for rel in ("groundtruth/groundtruth.json", "metric/container/kpi_container_cpu_usage_seconds_total.csv",
                    "metric/istio/kpi_istio_requests_total.csv", "metric/istio/kpi_istio_request_duration_milliseconds_sum.csv"):
            source_hashes[f"{case_name}/{rel}"] = sha256_file(case_dir / rel)
        for event in evts:
            event["overlapping_groundtruth_by_phase"] = {
                phase: phase_interventions(event, phase, all_events) for phase in PHASES}
    output = {
        "experiment_id": "wave-v3-cpu-trace-event-study-001",
        "model_id": MODEL_ID,
        "references": REFERENCES,
        "purpose": "Descriptive event study; trace latency is an external evaluation outcome and never a v3 input.",
        "design": "Group simultaneous same-type fault annotations into episodes; compare equal-duration before, during and after phases.",
        "phase_rule": "before=[start-duration,start); during=[start,end); after=[end,end+duration). Trace timestamps assigned by event timestamp.",
        "trace_duration_unit": "microseconds inferred from data representation; output milliseconds. Validate against Istio duration sums before confirmatory interpretation.",
        "trace_population": "type=request spans; target_service is cmdb_id equal to annotated service; root_request has empty parent_span. Sampling/completeness is unknown.",
        "percentile_rule": "nearest-rank empirical percentile, untrimmed; no interpolation",
        "events_by_case": episodes_by_case,
        "trace_summaries_ms": traces,
        "v3_summaries": feature_summary,
        "v3_features_csv_sha256": sha256_file(args.features_csv),
        "trace_scan_audit": audits,
        "source_hashes_sha256": source_hashes,
        "limitations": [
            "Trace rows identify service rather than the exact container instance; target-service latency is service-level.",
            "Same-time replicas under one fault injection are one episode, not independent replications.",
            "The sample rate/completeness of traces is not established by the CSV schema.",
            "No p95 value is inserted into the locked v3 formula; the v3 uses its specified mean-latency input.",
            "Event comparisons are observational around injected faults and do not establish CPU causality."
        ]
    }
    args.out.write_text(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "events": {k: len(v) for k, v in episodes_by_case.items()},
                      "trace_rows": {k: v["rows_read"] for k, v in audits.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
