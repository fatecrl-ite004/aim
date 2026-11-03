import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "experiments" / "wave_v3_cpu" / "run_trace_event_study.py"
SPEC = importlib.util.spec_from_file_location("wave_v3_trace_event_study", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TraceEventStudyTests(unittest.TestCase):
    def test_groups_simultaneous_replica_injections_into_one_episode(self):
        events = [
            {"timestamp": 100, "duration": 20, "failure_type": "cpu", "service": "currency", "cmdb_id": "currency-0"},
            {"timestamp": 100, "duration": 20, "failure_type": "cpu", "service": "currency", "cmdb_id": "currency-1"},
            {"timestamp": 160, "duration": 10, "failure_type": "delay", "service": "frontend", "cmdb_id": "frontend-0"},
            {"timestamp": 180, "duration": 10, "failure_type": "memory", "service": "frontend", "cmdb_id": "frontend-0"},
        ]
        result = MODULE.episodes(events)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["instances"], ["currency-0", "currency-1"])

    def test_phase_boundaries_are_half_open_and_duration_matched(self):
        event = {"start": 100, "end": 120, "duration": 20}
        self.assertEqual(MODULE.phase_for(80, event), "before")
        self.assertEqual(MODULE.phase_for(100, event), "during")
        self.assertEqual(MODULE.phase_for(120, event), "after")
        self.assertIsNone(MODULE.phase_for(140, event))

    def test_nearest_rank_percentile_is_deterministic(self):
        self.assertEqual(MODULE.percentile([5, 1, 4, 2, 3], .50), 3)
        self.assertEqual(MODULE.percentile([5, 1, 4, 2, 3], .95), 5)
        self.assertIsNone(MODULE.percentile([], .95))

    def test_trace_scan_preserves_event_windows_and_hashes_source(self):
        event = {"episode_id": "cpu-100", "start": 100, "end": 120, "duration": 20,
                 "services": ["currencyservice"], "instances": ["currencyservice-0"]}
        path = Path(__file__).resolve().parent / "fixtures" / "wave_v3_cpu" / "trace_event" / "trace.csv"
        result, audit = MODULE.read_trace_events(path, [event])
        self.assertEqual(result["durations_us"][("cpu-100", "during:target_service")], [20.0])
        self.assertEqual(result["durations_us"][("cpu-100", "during:root_request")], [30.0])
        self.assertEqual(audit["rows_read"], 4)
        self.assertEqual(len(audit["source_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
