import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aim_wave.aiopsarena import load_case


class AioPsArenaAdapterTests(unittest.TestCase):
    def test_pairs_by_edge_status_interval_and_marks_fault_overlap(self):
        root = Path(__file__).parent / "fixtures" / "wave_cpu_api" / "pairing_case"
        result = load_case(root)
        self.assertEqual(len(result["rows"]), 1)
        row = result["rows"][0]
        self.assertEqual(row["instance"], "checkout-0")
        self.assertEqual(row["api_matched_series_count"], 2)
        self.assertEqual(row["api_edge_count"], 1)
        self.assertTrue(row["cpu_fault_active"])
        self.assertEqual(row["wave"]["status"], "ok")
        self.assertEqual(row["wave"]["requests_total"], 10)
        self.assertEqual(row["wave"]["requests_failed"], 1)
        self.assertAlmostEqual(row["wave"]["latency_seconds"], 0.012)
        self.assertEqual(result["audit"]["join"]["unmatched_request_intervals"], 1)

    def test_counter_reset_is_excluded_and_counted(self):
        root = Path(__file__).parent / "fixtures" / "wave_cpu_api" / "reset_case"
        result = load_case(root)
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["audit"]["sources"]["cpu"]["reset_intervals"], 1)

    def test_observed_zero_delta_is_not_missing_api(self):
        root = Path(__file__).parent / "fixtures" / "wave_v3_cpu" / "zero_delta_case"
        result = load_case(root)
        self.assertEqual(len(result["rows"]), 1)
        row = result["rows"][0]
        self.assertEqual(row["api_edge_coverage"], "matched_api_series_zero_delta")
        self.assertEqual(row["observation"]["requests_total"], 0)
        self.assertEqual(row["wave"]["status"], "partial")


if __name__ == "__main__":
    unittest.main()
