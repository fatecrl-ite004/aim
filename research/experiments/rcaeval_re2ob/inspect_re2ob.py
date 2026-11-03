"""Create a schema-first inventory of local RCAEval RE2-OB CPU/delay cases."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from adapter import summarize_inventory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("research/reports/rcaeval_re2ob/generated/inventory.json"))
    args = parser.parse_args()
    report = summarize_inventory(args.dataset_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Found {report['case_count']} cases; inventory: {args.out}")
    if not report["cases"]:
        print("No RE2-OB CPU/delay data found. No Wave input was produced.")


if __name__ == "__main__":
    main()
