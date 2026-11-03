import ast
import importlib.util
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aim_wave.v3 import MODEL_ID, REFERENCES, derive


ROOT = Path(__file__).resolve().parents[2]


def wave_reference_derive():
    """Load only canonicalize/derive from the vendored Wave source, without pipeline deps."""
    source = ROOT / "research" / "vendor" / "wave-source" / "math" / "hypotenuse_lab" / "pipeline.py"
    experiment = ROOT / "research" / "vendor" / "wave-source" / "math" / "hypotenuse_lab" / "experiment.py"
    spec = importlib.util.spec_from_file_location("wave_v3_reference_experiment", experiment)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    tree = ast.parse(source.read_text(encoding="utf-8"))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"canonicalize", "derive"}]
    namespace = {"math": math, "MODEL_ID": "s-fixed-reference-quality-v3",
                 "REFERENCES": {"S_reference": 1.0, "throughput_per_second": 40.0, "latency_seconds": 0.1},
                 "BOUNDARY_RADIUS": math.sqrt(2-math.sqrt(2)), "BOUNDARY_ATOL": 1e-12,
                 "from_ratio": module.from_ratio}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec"), namespace)
    return namespace["derive"]


class WaveV3Tests(unittest.TestCase):
    def observation(self, cpu):
        return {"service": "api", "window_index": 0, "duration_seconds": 5,
                "completed": 100, "failed": 10, "mean_latency_seconds": 0.2,
                "cpu_cores": cpu, "counter_reset": False}

    def test_v3_port_matches_vendored_wave_reference_exactly(self):
        raw = self.observation(0.75)
        expected = wave_reference_derive()(raw, "fixture")
        actual = derive(raw, "fixture")
        self.assertEqual(actual, expected)

    def test_cpu_is_preserved_but_does_not_change_v3_geometry(self):
        low = derive(self.observation(0.1), "fixture")
        high = derive(self.observation(3.5), "fixture")
        self.assertEqual(low["cpu_cores"], 0.1)
        self.assertEqual(high["cpu_cores"], 3.5)
        for key in ("S", "P_raw", "P", "Q", "D", "theta", "alpha_raw", "alpha"):
            self.assertEqual(low[key], high[key])

    def test_v3_invariants_hold_and_cut_is_explicit(self):
        result = derive(self.observation(0.5), "fixture")
        self.assertEqual(result["model_id"], MODEL_ID)
        self.assertAlmostEqual(result["P"]**2 + result["Q"]**2, 1.0, places=14)
        self.assertAlmostEqual(result["D"]**2, 2.0 - 2.0*result["P"], places=14)
        cut = derive({**self.observation(0.5), "completed": 1000, "failed": 0,
                      "mean_latency_seconds": 0.05}, "fixture")
        self.assertTrue(cut["clipping_applied"])
        self.assertGreater(cut["P_raw"], cut["P"])

    def test_no_traffic_is_distinct_from_missing_input(self):
        idle = derive({**self.observation(0.0), "completed": 0, "failed": 0,
                       "mean_latency_seconds": None}, "fixture")
        missing = derive({**self.observation(0.0), "completed": None, "failed": None,
                          "mean_latency_seconds": None}, "fixture")
        self.assertEqual((idle["status"], idle["reason"]), ("partial", "no_traffic"))
        self.assertEqual((missing["status"], missing["reason"]), ("missing", "missing_counts"))

    def test_fractional_counts_are_rejected_not_rounded(self):
        result = derive({**self.observation(0.5), "completed": 4.5}, "fixture")
        self.assertEqual(result["reason"], "invalid_counts")

    def test_invalid_cpu_covariate_is_rejected(self):
        result = derive(self.observation(float("nan")), "fixture")
        self.assertEqual(result["reason"], "invalid_cpu_cores")


if __name__ == "__main__":
    unittest.main()
