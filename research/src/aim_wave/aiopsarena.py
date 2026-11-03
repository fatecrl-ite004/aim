"""Local, database-free adapter for selected AIOpsArena counters.

Istio request and duration series are paired by cmdb_id, suffix/status and
exact interval. Instance-prefix joining remains a provisional mapping.
"""
from __future__ import annotations
import csv, json, math
from collections import defaultdict
from pathlib import Path
from typing import Iterable
from .cpu_api import evaluate

DEFAULT_REFERENCES = {"cpu_reference_cores": 1.0, "latency_reference_seconds": 0.1,
                      "throughput_reference_per_second": 100.0}


def _read_series(path: Path, prefix: str) -> tuple[dict, dict]:
    series = defaultdict(list)
    audit = {"rows_read": 0, "malformed_rows": 0, "invalid_points": 0,
             "duplicate_points": 0, "reset_intervals": 0, "valid_intervals": 0,
             "interval_seconds": defaultdict(int)}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            audit["rows_read"] += 1
            if not row or not row.get("kpi_name") or not row.get("cmdb_id"):
                audit["malformed_rows"] += 1; continue
            name = row["kpi_name"]
            if not name.startswith(prefix): continue
            try:
                ts, val = int(row["timestamp"]), float(row["value"])
                if not math.isfinite(val): raise ValueError("non-finite")
            except (ValueError, TypeError, KeyError):
                audit["invalid_points"] += 1; continue
            series[(row["cmdb_id"], name[len(prefix):].lstrip("."))].append((ts, val))
    return series, audit


def _deltas(series: dict, audit: dict) -> Iterable[tuple[str, str, int, int, float]]:
    for (cmdb, suffix), points in series.items():
        points.sort()
        counts = defaultdict(list)
        for ts, val in points: counts[ts].append(val)
        duplicated = {ts for ts, vals in counts.items() if len(vals) > 1}
        audit["duplicate_points"] += sum(len(counts[ts]) for ts in duplicated)
        ordered = sorted((ts, vals[0]) for ts, vals in counts.items() if ts not in duplicated)
        for (t0, v0), (t1, v1) in zip(ordered, ordered[1:]):
            if t1 <= t0: continue
            if v1 < v0:
                audit["reset_intervals"] += 1; continue
            audit["valid_intervals"] += 1
            audit["interval_seconds"][t1-t0] += 1
            yield cmdb, suffix, t0, t1, v1-v0


def _groundtruth(path: Path) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    fields = ("timestamp", "service", "cmdb_id", "failure_type", "duration")
    if len({len(obj.get(f, [])) for f in fields}) != 1:
        raise ValueError("groundtruth columns have inconsistent lengths")
    return [{f: obj[f][i] for f in fields} for i in range(len(obj.get("timestamp", [])))]


def load_case(case_dir: Path, references: dict | None = None) -> dict:
    """Build joined per-instance windows and return rows plus audit counts."""
    refs = dict(DEFAULT_REFERENCES if references is None else references)
    root = case_dir / "metric"
    paths = {
        "cpu": (root/"container"/"kpi_container_cpu_usage_seconds_total.csv", "container_cpu_usage_seconds_total"),
        "requests": (root/"istio"/"kpi_istio_requests_total.csv", "istio_requests_total"),
        "duration": (root/"istio"/"kpi_istio_request_duration_milliseconds_sum.csv", "istio_request_duration_milliseconds_sum"),
    }
    audits = {}
    cpu_series, audits["cpu"] = _read_series(*paths["cpu"])
    cpu_windows, cpu_cmdb = {}, defaultdict(set)
    for cmdb, _, t0, t1, delta in _deltas(cpu_series, audits["cpu"]):
        instance = cmdb.removeprefix("observe."); key = (instance, t0, t1)
        cpu_windows[key] = cpu_windows.get(key, 0.0) + delta
        cpu_cmdb[key].add(cmdb)
    del cpu_series

    # Keep one request index while consuming the duration data, instead of
    # retaining full point and delta tables for every source simultaneously.
    request_series, audits["requests"] = _read_series(*paths["requests"])
    request_index = {(c,s,t0,t1): d for c,s,t0,t1,d in _deltas(request_series, audits["requests"])}
    del request_series
    request_count = len(request_index)
    duration_series, audits["duration"] = _read_series(*paths["duration"])
    join = {"request_series_intervals": request_count, "duration_series_intervals": 0,
            "matched_edge_status_intervals": 0, "unmatched_request_intervals": 0,
            "unmatched_duration_intervals": 0, "fractional_request_deltas": 0}
    api = defaultdict(lambda: {"total":0.0,"failed":0.0,"duration_ms":0.0,
                               "cmdb_ids":set(),"status_suffixes":set(),"pairs":0})
    for cmdb,suffix,t0,t1,duration_delta in _deltas(duration_series, audits["duration"]):
        join["duration_series_intervals"] += 1
        key = (cmdb,suffix,t0,t1)
        count_delta = request_index.pop(key, None)
        if count_delta is None:
            join["unmatched_duration_intervals"] += 1; continue
        if not math.isclose(count_delta, round(count_delta), rel_tol=0, abs_tol=1e-9):
            join["fractional_request_deltas"] += 1
        instance = cmdb.split(".",1)[0]
        agg = api[(instance,t0,t1)]
        agg["total"] += count_delta; agg["duration_ms"] += duration_delta
        agg["cmdb_ids"].add(cmdb); agg["status_suffixes"].add(suffix); agg["pairs"] += 1
        if not suffix.endswith("grpc.200.0"): agg["failed"] += count_delta
        join["matched_edge_status_intervals"] += 1
    join["unmatched_request_intervals"] = len(request_index)
    del duration_series, request_index
    cpu_keys, api_keys = set(cpu_windows), set(api)
    join["cpu_intervals_without_matched_api"] = len(cpu_keys-api_keys)
    join["api_intervals_without_cpu"] = len(api_keys-cpu_keys)

    events = _groundtruth(case_dir/"groundtruth"/"groundtruth.json")
    rows = []
    for (instance,t0,t1), cpu_delta in sorted(cpu_windows.items()):
        agg = api.get((instance,t0,t1))
        if agg is None:
            obs = {"window_seconds":t1-t0,"cpu_delta_seconds":cpu_delta,
                   "requests_total":None,"requests_failed":None,"mean_latency_seconds":None}
            coverage = "missing_matched_api_series"
        elif agg["total"] == 0:
            # An observed zero counter delta is no traffic, not missing telemetry.
            obs = {"window_seconds":t1-t0,"cpu_delta_seconds":cpu_delta,
                   "requests_total":0,"requests_failed":0,"mean_latency_seconds":None}
            coverage = "matched_api_series_zero_delta"
        else:
            obs = {"window_seconds":t1-t0,"cpu_delta_seconds":cpu_delta,
                   "requests_total":agg["total"],"requests_failed":agg["failed"],
                   "mean_latency_seconds":agg["duration_ms"]/agg["total"]/1000.0}
            coverage = "matched_edge_status_interval_instance_prefix_provisional"
        overlap = [e for e in events if e["cmdb_id"]==instance and e["timestamp"]<t1 and e["timestamp"]+e["duration"]>t0]
        cpu_overlap = [e for e in overlap if e["failure_type"]=="cpu"]
        rows.append({"case":case_dir.name,"instance":instance,
            "service":instance.rsplit("-",1)[0] if "-" in instance else instance,
            "window_start_epoch_seconds":t0,"window_end_epoch_seconds":t1,"window_seconds":t1-t0,
            "cpu_delta_seconds":cpu_delta,"cpu_cmdb_ids":sorted(cpu_cmdb[(instance,t0,t1)],
            ),"api_edge_cmdb_ids":sorted(agg["cmdb_ids"]) if agg else [],
            "api_status_suffixes":sorted(agg["status_suffixes"]) if agg else [],
            "api_edge_count":len(agg["cmdb_ids"]) if agg else 0,
            "api_matched_series_count":agg["pairs"] if agg else 0,"api_edge_coverage":coverage,
            "cpu_fault_active":bool(cpu_overlap),
            "cpu_fault_episode_start":min((e["timestamp"] for e in cpu_overlap),default=None),
            "overlapping_cpu_events":cpu_overlap,"groundtruth_faults":sorted({e["failure_type"] for e in overlap}),
            "observation":obs,"wave":evaluate(obs,refs)})
    return {"rows":rows,"audit":{"sources":audits,"join":join},"groundtruth_events":events}
