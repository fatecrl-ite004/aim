import json
import unittest
from pathlib import Path

import pandas as pd

from research.experiments.rcaeval_re2ob.adapter import (
    inventory_case, parse_case_name, read_metrics, summarize_inventory,
)
from research.experiments.rcaeval_re2ob.download_cpu_delay_subset import select_case_files
from research.experiments.rcaeval_re2ob.run_wave_v3_source_aligned import process_case

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "rcaeval_re2ob"


class RCAEvalRE2OBTests(unittest.TestCase):
    def test_case_name_parsing_and_scope(self):
        self.assertEqual(parse_case_name("re2ob_checkoutservice_cpu_2")["repetition"], 2)
        self.assertIsNone(parse_case_name("re2ob_checkoutservice_mem_2"))

    def test_subset_selection_requires_complete_cpu_delay_suite(self):
        paths = [f"re2ob/cases/re2ob_svc_{fault}_{rep}/metrics.parquet"
                 for fault in ("cpu", "delay") for rep in range(1, 16)]
        self.assertEqual(len(select_case_files(paths)), 30)
        with self.assertRaises(RuntimeError):
            select_case_files(paths[:-1])

    def test_metrics_timestamp_union_keeps_gaps_and_nulls(self):
        case = FIXTURE_ROOT / "re2ob_checkoutservice_cpu_1"
        case.mkdir(parents=True, exist_ok=True)
        (case / "metrics.json").write_text(json.dumps({
                "checkoutservice_cpu_usage": [[100, 0.2], [110, 0.5]],
                "checkoutservice_request_rate": [[105, 10]],
        }))
        frame = read_metrics(case)
        self.assertEqual(frame["time"].tolist(), [100, 105, 110])
        self.assertTrue(frame["checkoutservice_cpu_usage"].isna().iloc[1])
        self.assertTrue(frame["checkoutservice_request_rate"].isna().iloc[0])

    def test_inventory_marks_name_match_as_candidate_only(self):
        case = FIXTURE_ROOT / "re2ob_checkoutservice_cpu_1"
        case.mkdir(parents=True, exist_ok=True)
        (case / "metrics.json").write_text(json.dumps({
                "cpu_usage": [[100, 0.2], [105, 0.8]],
                "request_latency": [[100, 0.05], [105, 0.2]],
        }))
        (case / "inject_time.txt").write_text("105")
        (case / "traces.csv").write_text("traceID,duration,statusCode\na,100,200\n")
        result = inventory_case(case)
        self.assertEqual(result["rows_before_injection"], 1)
        self.assertEqual(result["rows_at_or_after_injection"], 1)
        self.assertIn("request_latency", result["name_only_candidates_not_semantic_mappings"]["latency_name_candidates"])
        self.assertEqual(result["trace"]["rows"], 1)

    def test_empty_dataset_is_explicitly_not_a_result(self):
        result = summarize_inventory(FIXTURE_ROOT / "empty")
        self.assertEqual(result["case_count"], 0)
        self.assertFalse(result["metric_semantics_confirmed"])
        self.assertEqual(result["recommendation"], "inventory_only_no_case_data_found")

    def test_wave_api_operation_ignores_nested_calls_and_keeps_unknown_errors_missing(self):
        case = FIXTURE_ROOT / "re2ob_checkoutservice_cpu_99"
        case.mkdir(parents=True, exist_ok=True)
        start = 1_700_000_000
        pd.DataFrame({"time": [start, start + 60], "checkoutservice_cpu": [2.0, 4.0]}).to_parquet(case / "metrics.parquet")
        pd.DataFrame([
            {"serviceName": "frontendservice", "operationName": "frontend", "parentSpanID": "",
             "startTime": start * 1_000_000 + 100, "duration": 100_000, "statusCode": pd.NA},
            {"serviceName": "frontendservice", "operationName": "hipstershop.CartService/GetCart",
             "parentSpanID": "parent", "startTime": start * 1_000_000 + 200, "duration": 5_000, "statusCode": 0},
        ]).to_parquet(case / "traces.parquet")
        (case / "inject_time.txt").write_text(str(start + 30), encoding="utf-8")
        try:
            rows = process_case(case)
            self.assertEqual(rows[0]["trace_request_spans"], 1)
            self.assertEqual(rows[0]["mean_span_duration_seconds"], 0.1)
            self.assertIsNone(rows[0]["trace_errors_by_rcaeval_rule"])
            self.assertEqual(rows[0]["status"], "missing")
            self.assertIsNone(rows[0]["P"])
            self.assertEqual(rows[0]["cpu_metric_raw_mean_candidate"], 2.0)
            self.assertIsNone(rows[0]["cpu_cores_input"])
        finally:
            for filename in ("metrics.parquet", "traces.parquet", "inject_time.txt"):
                (case / filename).unlink(missing_ok=True)
            case.rmdir()


if __name__ == "__main__":
    unittest.main()
