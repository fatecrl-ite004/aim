import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aim_wave.cpu_api import evaluate, encode_wave

REF = {"cpu_reference_cores": 1.0, "latency_reference_seconds": 0.1,
       "throughput_reference_per_second": 100.0}


class CpuApiWaveTests(unittest.TestCase):
    def test_cpu_api_formula_and_polar_round_trip(self):
        row = evaluate({"window_seconds": 5, "cpu_delta_seconds": 2.5,
                        "requests_total": 100, "requests_failed": 10,
                        "mean_latency_seconds": 0.2}, REF)
        self.assertEqual(row["status"], "ok")
        self.assertAlmostEqual(row["A_cpu_normalized"], 0.5)
        self.assertAlmostEqual(row["throughput_per_second"], 20.0)
        self.assertAlmostEqual(row["error_percent"], 10.0)
        self.assertAlmostEqual(row["P_api"], 0.09)
        self.assertAlmostEqual(row["R"] * math.cos(row["phi_radians"]), row["A_cpu_normalized"])
        self.assertAlmostEqual(row["R"] * math.sin(row["phi_radians"]), row["P_api"])

    def test_cpu_and_api_coordinates_are_not_clipped(self):
        row = evaluate({"window_seconds": 5, "cpu_delta_seconds": 7.5,
                        "requests_total": 1200, "requests_failed": 0,
                        "mean_latency_seconds": 0.1}, REF)
        self.assertEqual(row["status"], "ok")
        self.assertAlmostEqual(row["A_cpu_normalized"], 1.5)
        self.assertAlmostEqual(row["P_api"], 2.4)

    def test_fractional_counter_delta_is_preserved(self):
        row = evaluate({"window_seconds": 5, "cpu_delta_seconds": 1,
                        "requests_total": 10.25, "requests_failed": 0.25,
                        "mean_latency_seconds": 0.05}, REF)
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["requests_total"], 10.25)
        self.assertEqual(row["requests_failed"], 0.25)

    def test_missing_api_is_partial_not_zero(self):
        row = evaluate({"window_seconds": 5, "cpu_delta_seconds": 2.5}, REF)
        self.assertEqual(row["status"], "partial")
        self.assertAlmostEqual(row["A_cpu_normalized"], 0.5)
        self.assertIsNone(row["P_api"])
        self.assertIsNone(row["R"])

    def test_zero_vector_uses_convention_and_marks_phase_unidentifiable(self):
        row = evaluate({"window_seconds": 5, "cpu_delta_seconds": 0,
                        "requests_total": 100, "requests_failed": 100,
                        "mean_latency_seconds": 0.1}, REF)
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["R"], 0)
        self.assertEqual(row["phi_radians"], 0)
        self.assertFalse(row["phase_identifiable"])

    def test_nonpositive_window_rejected(self):
        row = evaluate({"window_seconds": 0, "cpu_delta_seconds": 0}, REF)
        self.assertEqual(row["reason"], "invalid_window")

    def test_wave_carrier_uses_documented_coordinates(self):
        self.assertAlmostEqual(encode_wave(1.0, 0.0, 0.0), 1.0)
        self.assertAlmostEqual(encode_wave(0.0, 1.0, 0.25), 1.0)


if __name__ == "__main__":
    unittest.main()
