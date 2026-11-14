"""Local commands; dataset, labels, transmission and batch stay explicit stages."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .dataset import audit_cut, load_cut, load_ground_truth


def _print_result(result: dict[str, Any], output: Path | None) -> None:
    serialized = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


def main() -> None:
    parser = argparse.ArgumentParser(description="AIM V1 historical replay and PostgreSQL batch")
    parser.add_argument("--env-file", type=Path, default=Path(__file__).resolve().parents[3] / ".env.v1")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "replay", "stream", "verify", "import-ground-truth", "transform", "transform-60s"):
        command = commands.add_parser(name)
        command.add_argument("--output", type=Path)
        if name not in ("transform", "transform-60s"):
            command.add_argument("--dataset-root", type=Path)
        if name in ("verify", "import-ground-truth", "transform", "transform-60s"):
            command.add_argument("--replay-id", required=True)
        if name in ("replay", "stream"):
            command.add_argument("--api-url")
        if name == "replay":
            command.add_argument("--replay-id", help="Reuse a replay ID to verify retry idempotency")
        if name == "stream":
            command.add_argument("--chunk-timestamps", type=int, default=8,
                                 help="Source timestamps per OTLP request (all selected series share this grid)")
            command.add_argument("--pause-seconds", type=float, default=3.0,
                                 help="Pause between later milestones so the historical replay visibly advances")
            command.add_argument("--initial-pause-seconds", type=float, default=15.0,
                                 help="Pause after the first transformed milestone so the UI can be opened")
            command.add_argument("--transform-every-chunks", type=int, default=1,
                                 help="Create a new persisted transform run every N chunks; the last chunk always transforms")
    arguments = parser.parse_args()
    load_dotenv(arguments.env_file)
    if arguments.command in ("transform", "transform-60s"):
        from .repository import Repository
        from .transform import run_transform, run_transform_60s
        transform = run_transform_60s if arguments.command == "transform-60s" else run_transform
        result = transform(Repository(), arguments.replay_id)
    else:
        dataset_root = arguments.dataset_root or (Path(os.environ["AIM_DATASET_ROOT"]) if os.environ.get("AIM_DATASET_ROOT") else None)
        if not dataset_root:
            parser.error("Pass --dataset-root or configure AIM_DATASET_ROOT; source files remain external")
        if arguments.command == "import-ground-truth":
            from .repository import Repository
            repository = Repository()
            replay = repository.get_replay(arguments.replay_id)
            if replay is None:
                raise ValueError("Replay not found")
            source_sha256, events = load_ground_truth(dataset_root)
            manifest = replay["source_manifest"]
            matching = [file for file in manifest["files"] if file["role"] == "ground_truth"]
            if len(matching) != 1 or matching[0]["sha256"] != source_sha256:
                raise ValueError("Ground truth hash differs from the replay source manifest")
            result = repository.import_ground_truth(arguments.replay_id, events)
            result = {"replay_run_id": arguments.replay_id, "stage": "separate_ground_truth_import", "event_type": "injected_fault", "source_file_sha256": source_sha256, "event_count": len(events), "result": result}
        else:
            cut = load_cut(dataset_root)
            if arguments.command == "audit":
                result = audit_cut(cut)
                result["license_files_in_dataset_root"] = [file.name for file in dataset_root.iterdir() if any(term in file.name.lower() for term in ("license", "copying", "notice"))]
            elif arguments.command == "replay":
                from .replay import send_replay
                result = send_replay(cut, arguments.api_url or os.environ.get("AIM_API_URL", "http://127.0.0.1:8000"), arguments.replay_id)
            elif arguments.command == "stream":
                from .progressive import run_progressive

                def report_progress(update: dict[str, Any]) -> None:
                    print(json.dumps(update, ensure_ascii=False), flush=True)

                result = run_progressive(
                    dataset_root, arguments.api_url or os.environ.get("AIM_API_URL", "http://127.0.0.1:8000"),
                    cut=cut, metrics_endpoint=os.environ.get("AIM_OTLP_METRICS_ENDPOINT"),
                    chunk_timestamps=arguments.chunk_timestamps,
                    pause_seconds=arguments.pause_seconds,
                    initial_pause_seconds=arguments.initial_pause_seconds,
                    transform_every_chunks=arguments.transform_every_chunks,
                    on_progress=report_progress,
                )
            else:
                from .repository import Repository
                from .replay import verify_persisted
                result = {"replay_run_id": arguments.replay_id, **verify_persisted(cut, Repository().get_raw_points(arguments.replay_id))}
    _print_result(result, arguments.output)


if __name__ == "__main__":
    main()
