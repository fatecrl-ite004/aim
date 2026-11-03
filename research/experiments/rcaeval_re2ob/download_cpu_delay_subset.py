"""Download only the RE2-OB CPU and delay case data from Hugging Face."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ID = "phamquiluan/RCAEval"
CASE_DIR = re.compile(r"(?:^|/)re2ob_[^/]+_(?:cpu|delay)_\d+$")


def select_case_files(paths: list[str]) -> list[str]:
    """Return all files belonging to CPU/delay cases, excluding unrelated suite data."""
    selected = [path for path in paths if CASE_DIR.search(path.rsplit("/", 1)[0])]
    cases = {path.rsplit("/", 1)[0] for path in selected}
    if len(cases) != 30:
        raise RuntimeError(f"Expected 30 RE2-OB CPU/delay cases, found {len(cases)}")
    for fault in ("cpu", "delay"):
        fault_cases = [case for case in cases if re.search(rf"_{fault}_\d+$", case)]
        if len(fault_cases) != 15:
            raise RuntimeError(f"Expected 15 {fault} cases, found {len(fault_cases)}")
    return sorted(selected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("research/data/rcaeval/re2ob_cpu_delay"))
    args = parser.parse_args()
    from huggingface_hub import HfApi, snapshot_download

    paths = HfApi().list_repo_files(REPO_ID, repo_type="dataset")
    selected = select_case_files(paths)
    args.out.mkdir(parents=True, exist_ok=True)
    snapshot_download(REPO_ID, repo_type="dataset", allow_patterns=selected, local_dir=str(args.out))
    manifest = {"repo_id": REPO_ID, "selected_case_files": selected,
                "case_count": len({p.rsplit("/", 1)[0] for p in selected}),
                "faults": ["cpu", "delay"], "downloaded_at_utc": None,
                "note": "Manifest lists selected paths; no metrics semantics are asserted."}
    (args.out / "download_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Downloaded {manifest['case_count']} cases ({len(selected)} files) to {args.out}")


if __name__ == "__main__":
    main()
