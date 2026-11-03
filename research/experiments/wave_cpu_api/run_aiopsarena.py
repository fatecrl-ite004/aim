"""Run the exploratory Wave CPU/API candidate on local AIOpsArena cases."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "research" / "src"))
from aim_wave.aiopsarena import DEFAULT_REFERENCES, load_case  # noqa: E402


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = rank
        i = j
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    x, y = average_ranks(xs), average_ranks(ys)
    mx, my = sum(x)/len(x), sum(y)/len(y)
    cov = sum((a-mx)*(b-my) for a,b in zip(x,y))
    dx = math.sqrt(sum((a-mx)**2 for a in x))
    dy = math.sqrt(sum((b-my)**2 for b in y))
    return cov/(dx*dy) if dx and dy else None


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean(values: list[float]) -> float | None:
    return sum(values)/len(values) if values else None


def summarize(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        if row["wave"]["status"] == "ok":
            groups[(row["case"], row["instance"])].append(row)
    result = []
    comparisons = {
        "cpu_vs_latency_mean_s": ("cpu_percent_of_reference", "latency_seconds"),
        "cpu_vs_throughput_rps": ("cpu_percent_of_reference", "throughput_per_second"),
        "cpu_vs_grpc_error_percent": ("cpu_percent_of_reference", "error_percent"),
        "cpu_vs_wave_P_composite": ("cpu_percent_of_reference", "P_api"),
    }
    for (case, instance), group in sorted(groups.items()):
        fault = [r for r in group if r["cpu_fault_active"]]
        control = [r for r in group if not r["cpu_fault_active"]]
        correlations = {}
        for name, (xkey, ykey) in comparisons.items():
            pairs = [(float(r["wave"][xkey]), float(r["wave"][ykey])) for r in group
                     if r["wave"].get(xkey) is not None and r["wave"].get(ykey) is not None]
            correlations[name] = {"n_windows": len(pairs),
                                  "rho": spearman([p[0] for p in pairs], [p[1] for p in pairs])}
        result.append({
            "case": case, "instance": instance, "service": group[0]["service"],
            "valid_joined_windows": len(group), "cpu_fault_windows": len(fault), "non_cpu_fault_windows": len(control),
            "cpu_fault_episode_starts": sorted({r["cpu_fault_episode_start"] for r in fault if r["cpu_fault_episode_start"] is not None}),
            "mean_cpu_pct_reference_fault": mean([r["wave"]["cpu_percent_of_reference"] for r in fault]),
            "mean_cpu_pct_reference_control": mean([r["wave"]["cpu_percent_of_reference"] for r in control]),
            "mean_latency_s_fault": mean([r["wave"]["latency_seconds"] for r in fault]),
            "mean_latency_s_control": mean([r["wave"]["latency_seconds"] for r in control]),
            "mean_throughput_fault": mean([r["wave"]["throughput_per_second"] for r in fault]),
            "mean_throughput_control": mean([r["wave"]["throughput_per_second"] for r in control]),
            "mean_error_pct_fault": mean([r["wave"]["error_percent"] for r in fault]),
            "mean_error_pct_control": mean([r["wave"]["error_percent"] for r in control]),
            "mean_wave_R_all": mean([r["wave"]["R"] for r in group]),
            "spearman": correlations,
        })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True, help="Folder containing Case-1/Case-1 and Case-2/Case-2")
    parser.add_argument("--out", type=Path, default=REPO / "research" / "reports" / "wave_cpu_api" / "generated")
    args = parser.parse_args()
    all_rows, audits, hashes, event_summary = [], {}, {}, {}
    for case in ("Case-1", "Case-2"):
        case_dir = args.dataset_root / case / case
        if not case_dir.exists():
            raise FileNotFoundError(f"expected AIOpsArena layout for {case}: {case_dir}")
        loaded = load_case(case_dir, DEFAULT_REFERENCES)
        all_rows.extend(loaded["rows"])
        audits[case] = loaded["audit"]
        events = loaded["groundtruth_events"]
        event_summary[case] = {
            "cpu_groundtruth_rows": sum(e["failure_type"] == "cpu" for e in events),
            "cpu_episode_keys": sorted({(e["timestamp"], e["service"], e["failure_type"]) for e in events if e["failure_type"] == "cpu"}),
        }
        for key in (
            "metric/container/kpi_container_cpu_usage_seconds_total.csv",
            "metric/istio/kpi_istio_requests_total.csv",
            "metric/istio/kpi_istio_request_duration_milliseconds_sum.csv",
            "groundtruth/groundtruth.json",
        ):
            path = case_dir / key
            hashes[f"{case}/{key.replace(chr(47), chr(92))}"] = hash_file(path)
    args.out.mkdir(parents=True, exist_ok=True)
    cols = ["case","service","instance","window_start_epoch_seconds","window_end_epoch_seconds","window_seconds",
            "cpu_delta_seconds","cpu_cmdb_ids","api_edge_cmdb_ids","api_status_suffixes","api_edge_count",
            "api_matched_series_count","api_edge_coverage","cpu_fault_active","cpu_fault_episode_start","groundtruth_faults",
            "status","reason","requests_total","requests_failed","throughput_per_second","error_percent",
            "latency_seconds","A_cpu_normalized","cpu_percent_of_reference","P_api","R","phi_radians","phase_identifiable"]
    csv_path = args.out / "wave_cpu_api_windows.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=cols)
        writer.writeheader()
        for row in all_rows:
            w = row["wave"]
            observation = row["observation"]
            episodes = sorted({e["timestamp"] for e in row["overlapping_cpu_events"]}) if "overlapping_cpu_events" in row else []
            record = {"case":row["case"],"service":row["service"],"instance":row["instance"],
                "window_start_epoch_seconds":row["window_start_epoch_seconds"],"window_end_epoch_seconds":row["window_end_epoch_seconds"],
                "window_seconds":row["window_seconds"],"cpu_delta_seconds":row["cpu_delta_seconds"],
                "cpu_cmdb_ids":";".join(row["cpu_cmdb_ids"]),"api_edge_cmdb_ids":";".join(row["api_edge_cmdb_ids"]),
                "api_status_suffixes":";".join(row["api_status_suffixes"]),"api_edge_count":row["api_edge_count"],
                "api_matched_series_count":row["api_matched_series_count"],"api_edge_coverage":row["api_edge_coverage"],
                "cpu_fault_active":row["cpu_fault_active"],"cpu_fault_episode_start":";".join(map(str,episodes)),
                "groundtruth_faults":";".join(row["groundtruth_faults"]),"status":w["status"],"reason":w["reason"],
                "requests_total":observation.get("requests_total"),"requests_failed":observation.get("requests_failed"),
                **{k:w.get(k) for k in ("throughput_per_second","error_percent","latency_seconds","A_cpu_normalized",
                    "cpu_percent_of_reference","P_api","R","phi_radians","phase_identifiable")}}
            writer.writerow(record)
    summary = {
        "experiment_id":"wave-cpu-api-aiopsarena-exploratory-001","model_id":"wave-cpu-api-harmonic-v0.1",
        "source":"AIOpsArena local Case-1 and Case-2; original files not copied into AIM",
        "references":DEFAULT_REFERENCES,
        "reference_note":"Exploratory Wave README references, not SLOs/capacity, fixed before this execution.",
        "cadence_note":"Use observed intervals (expected about 15 s); do not resample to laboratory 5 s.",
        "join_assumption":"Istio edge cmdb_id prefix is provisionally treated as the corresponding container instance. Preserve all original edge IDs; aggregation may still include semantically overlapping directions.",
        "api_error_rule":"gRPC status 0 suffix is success; other observed statuses count as errors for this exploratory measure only.",
        "latency_rule":"same edge/status/interval duration-sum delta divided by request-count delta; milliseconds converted to seconds. Mean only, no p95.",
        "groundtruth_events":event_summary,"source_hashes_sha256":hashes,"adapter_audit":audits,
        "input_window_rows":len(all_rows),"joined_valid_rows":sum(r["wave"]["status"]=="ok" for r in all_rows),
        "partial_or_invalid_rows":sum(r["wave"]["status"]!="ok" for r in all_rows),
        "summary_by_case_instance":summarize(all_rows),"window_features_csv":csv_path.name,
        "interpretation":"Descriptive Spearman associations on autocorrelated windows only; no p-values, causal or detector-quality claims. CPU vs P is composite; interpret raw outcome correlations separately."
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"out":str(args.out),"input_window_rows":len(all_rows),"joined_valid_rows":summary["joined_valid_rows"],"partial_or_invalid_rows":summary["partial_or_invalid_rows"]},ensure_ascii=False))


if __name__ == "__main__":
    main()
