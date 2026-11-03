"""Run Wave v3 unchanged, carrying CPU as a covariate, on local AIOpsArena."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "research" / "src"))
sys.path.insert(0, str(REPO / "research" / "experiments" / "wave_cpu_api"))

from aim_wave.aiopsarena import load_case  # noqa: E402
from aim_wave.v3 import MODEL_ID, REFERENCES, derive  # noqa: E402
from run_aiopsarena import hash_file, mean, spearman  # noqa: E402


def summarize(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if row["v3"]["status"] == "ok":
            grouped[(row["case"], row["instance"])].append(row)
    comparisons = {
        "cpu_vs_api_latency_mean_s": ("cpu_cores", "latency_seconds"),
        "cpu_vs_api_throughput_rps": ("cpu_cores", "throughput_rps"),
        "cpu_vs_api_error_percent": ("cpu_cores", "error_percent"),
        "cpu_vs_v3_P": ("cpu_cores", "P"),
        "cpu_vs_v3_D": ("cpu_cores", "D"),
    }
    result = []
    for (case, instance), group in sorted(grouped.items()):
        fault = [r for r in group if r["cpu_fault_active"]]
        control = [r for r in group if not r["cpu_fault_active"]]
        correlations = {}
        for name, (xkey, ykey) in comparisons.items():
            pairs = [(float(r["v3"][xkey]), float(r["v3"][ykey]))
                     for r in group if r["v3"].get(xkey) is not None and r["v3"].get(ykey) is not None]
            correlations[name] = {"n_windows": len(pairs),
                                  "rho": spearman([p[0] for p in pairs], [p[1] for p in pairs])}
        result.append({
            "case": case, "instance": instance, "service": group[0]["service"],
            "valid_v3_windows": len(group), "cpu_fault_windows": len(fault),
            "control_windows": len(control),
            "mean_cpu_cores_fault": mean([r["v3"]["cpu_cores"] for r in fault]),
            "mean_cpu_cores_control": mean([r["v3"]["cpu_cores"] for r in control]),
            "mean_latency_seconds_fault": mean([r["v3"]["latency_seconds"] for r in fault]),
            "mean_latency_seconds_control": mean([r["v3"]["latency_seconds"] for r in control]),
            "mean_throughput_rps_fault": mean([r["v3"]["throughput_rps"] for r in fault]),
            "mean_throughput_rps_control": mean([r["v3"]["throughput_rps"] for r in control]),
            "mean_error_percent_fault": mean([r["v3"]["error_percent"] for r in fault]),
            "mean_error_percent_control": mean([r["v3"]["error_percent"] for r in control]),
            "mean_P_fault": mean([r["v3"]["P"] for r in fault]),
            "mean_P_control": mean([r["v3"]["P"] for r in control]),
            "mean_D_fault": mean([r["v3"]["D"] for r in fault]),
            "mean_D_control": mean([r["v3"]["D"] for r in control]),
            "spearman": correlations,
        })
    return result


def make_v3_row(row: dict, index: int) -> dict:
    obs = row["observation"]
    n, f = obs["requests_total"], obs["requests_failed"]
    if n is not None and math.isclose(n, round(n), rel_tol=0, abs_tol=1e-9):
        n = int(round(n))
    if f is not None and math.isclose(f, round(f), rel_tol=0, abs_tol=1e-9):
        f = int(round(f))
    raw = {
        "service": row["service"], "window_index": index,
        "start_utc": row["window_start_epoch_seconds"], "end_utc": row["window_end_epoch_seconds"],
        "duration_seconds": row["window_seconds"], "completed": n, "failed": f,
        "mean_latency_seconds": obs["mean_latency_seconds"],
        "cpu_cores": row["cpu_delta_seconds"] / row["window_seconds"],
        "counter_reset": False,
        "source_identity": {"case": row["case"], "instance": row["instance"],
                            "cpu_cmdb_ids": row["cpu_cmdb_ids"],
                            "api_edge_cmdb_ids": row["api_edge_cmdb_ids"],
                            "api_status_suffixes": row["api_status_suffixes"]},
    }
    result = derive(raw, "aiopsarena_observed_metrics", REFERENCES)
    # Keep raw API/CPU measures next to the v3 indices for independent comparisons.
    result["cpu_cores"] = raw["cpu_cores"]
    result["throughput_rps"] = (n / row["window_seconds"] if isinstance(n, int) and row["window_seconds"] > 0 else None)
    result["error_percent"] = (100.0 * f / n if isinstance(n, int) and n > 0 and isinstance(f, int) else None)
    result["latency_seconds"] = raw["mean_latency_seconds"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True,
                        help="Folder containing Case-1/Case-1 and Case-2/Case-2")
    parser.add_argument("--out", type=Path, default=REPO / "research" / "reports" / "wave_v3_cpu" / "generated")
    args = parser.parse_args()
    rows: list[dict] = []
    audits: dict = {}
    hashes: dict = {}
    for case in ("Case-1", "Case-2"):
        case_dir = args.dataset_root / case / case
        if not case_dir.exists():
            raise FileNotFoundError(f"expected AIOpsArena layout for {case}: {case_dir}")
        loaded = load_case(case_dir)
        audits[case] = loaded["audit"]
        per_instance_index: dict[str, int] = defaultdict(int)
        for base_row in loaded["rows"]:
            idx = per_instance_index[base_row["instance"]]
            per_instance_index[base_row["instance"]] += 1
            rows.append({**base_row, "v3": make_v3_row(base_row, idx)})
        for rel in (
            "metric/container/kpi_container_cpu_usage_seconds_total.csv",
            "metric/istio/kpi_istio_requests_total.csv",
            "metric/istio/kpi_istio_request_duration_milliseconds_sum.csv",
            "groundtruth/groundtruth.json",
        ):
            hashes[f"{case}/{rel.replace('/', chr(92))}"] = hash_file(case_dir / rel)

    args.out.mkdir(parents=True, exist_ok=True)
    cols = ["case", "service", "instance", "window_start_epoch_seconds", "window_end_epoch_seconds",
            "window_seconds", "status", "reason", "operational_state", "cpu_cores", "completed", "failed",
            "goodput_per_second", "throughput_rps", "error_percent", "latency_seconds", "S", "P_raw", "P",
            "Q", "D", "theta", "alpha_raw", "alpha", "quality_factor", "clipping_applied",
            "restriction_delta", "boundary_status", "cpu_fault_active", "cpu_fault_episode_start",
            "api_edge_coverage", "api_edge_cmdb_ids"]
    csv_path = args.out / "wave_v3_cpu_windows.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            v3 = row["v3"]
            record = {"case": row["case"], "service": row["service"], "instance": row["instance"],
                      "window_start_epoch_seconds": row["window_start_epoch_seconds"],
                      "window_end_epoch_seconds": row["window_end_epoch_seconds"],
                      "window_seconds": row["window_seconds"], "cpu_fault_active": row["cpu_fault_active"],
                      "cpu_fault_episode_start": row["cpu_fault_episode_start"],
                      "api_edge_coverage": row["api_edge_coverage"],
                      "api_edge_cmdb_ids": ";".join(row["api_edge_cmdb_ids"])}
            record.update({k: v3.get(k) for k in cols if k in v3})
            writer.writerow(record)

    counts = defaultdict(int)
    for row in rows:
        counts[(row["case"], row["v3"]["status"], row["v3"]["reason"] or "none")] += 1
    summary = {
        "experiment_id": "wave-v3-cpu-covariate-aiopsarena-001", "model_id": MODEL_ID,
        "source": "AIOpsArena local Case-1/Case-2; raw dataset not copied into AIM",
        "references": REFERENCES,
        "mathematical_contract": "Unmodified Wave v3: S=1; P derives from goodput and mean latency; Q is geometric residual; D=hypot(P-1,Q). CPU cores are preserved covariates and do not enter S/P/Q/D.",
        "cpu_definition": "cpu_cores = delta(container_cpu_usage_seconds_total) / observed_interval_seconds; no clipping; one core is a reference unit, not a pod limit.",
        "cadence": "Observed intervals, predominantly 15 seconds; no resampling to 5 seconds.",
        "api_mapping": "Provisional cmdb_id instance-prefix join; per edge/status/interval pairing is audited in the shared adapter.",
        "source_hashes_sha256": hashes, "adapter_audit": audits,
        "input_windows": len(rows), "status_counts": {"|".join(map(str, k)): v for k, v in sorted(counts.items())},
        "valid_v3_windows": sum(r["v3"]["status"] == "ok" for r in rows),
        "summary_by_case_instance": summarize(rows),
        "window_features_csv": csv_path.name,
        "interpretation": "Association-only report; no causal/predictive/detector-performance claims. CPU never changes v3 geometry.",
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "input_windows": len(rows),
                      "valid_v3_windows": summary["valid_v3_windows"], "status_counts": summary["status_counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
