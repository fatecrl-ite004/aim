"""Inventory AD-microservice-app and produce a cautious CPU/FIS event study."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from adapter import event_study, inventory_day, sha256


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("research/reports/ad_microservice_app/generated"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report_days = []
    all_events = []
    for day in ("13-05-2024", "20-05-2024"):
        day_dir = args.dataset_root / day
        summary, metrics, _ = inventory_day(day_dir)
        metric_path = day_dir / f"{day}_metrics.csv"
        action_path = day_dir / f"{day}_FIS_Experiment_Actions.csv"
        summary["source_hashes_sha256"] = {metric_path.name: sha256(metric_path), action_path.name: sha256(action_path)}
        results = event_study(summary, metrics)
        event_path = args.out / f"{day}_cpu_event_study.json"
        event_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        summary["event_study_path"] = event_path.name
        summary["event_study_rows"] = len(results)
        clean_results = [r for r in results if not r["overlapping_experiment_ids"]]
        summary["event_study_nonoverlap_rows"] = len(clean_results)
        summary["front_end_candidate_phase_medians"] = {
            phase: {
                signal: (statistics.median(values) if values else None)
                for signal in ("front-end_req_rate", "front-end_req_ok", "front-end_req_ko",
                               "front-end_avg_rt", "front-end_avg_ok_rt")
                for values in [[r[f"{phase}_median__{signal}"] for r in clean_results
                                if r.get(f"{phase}_median__{signal}") is not None]]
            }
            for phase in ("pre", "during", "post")
        }
        summary["wave_v3_executed"] = False
        summary["wave_v3_gate"] = "Request completion/failure semantics and response-time unit are not confirmed; source columns are internally inconsistent for completed/failed mapping."
        report_days.append(summary)
        all_events.extend({"dataset_day": day, **r} for r in results)
    report = {
        "dataset": "AD-microservice-app synthetic time series",
        "days": report_days,
        "event_study": "CPU-stress episodes compared with candidate front-end request/response metrics in 5-minute pre, during and post phases.",
        "wave_v3_executed": False,
        "interpretation": "Descriptive co-occurrence only. CPU metrics and API fields are not assigned units by this adapter; labels identify anomaly/FIS intervals, not API impact.",
    }
    (args.out / "inventory_and_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"days": len(report_days), "actions": sum(d["action_count"] for d in report_days),
                      "cpu_actions": sum(d["cpu_action_count"] for d in report_days),
                      "wave_v3_executed": False, "out": str(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
