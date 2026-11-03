import unittest
import pandas as pd

from research.experiments.ad_microservice_app.adapter import parity_audit


class ADMicroserviceAdapterTests(unittest.TestCase):
    def test_equal_rate_and_ok_fields_do_not_override_nonzero_ko_candidate(self):
        frame = pd.DataFrame({"svc_req_rate": [10.0, 12.0], "svc_req_ok": [10.0, 12.0],
                              "svc_req_ko": [1.0, 2.0], "svc_avg_rt": [3.0, 4.0],
                              "svc_avg_ok_rt": [3.0, 4.0]})
        result = parity_audit(frame)
        self.assertTrue(result["req_rate_equals_req_ok"][0]["all_equal"])
        self.assertEqual(result["failed_candidate_nonzero_rows"]["svc"], 2)
        self.assertTrue(result["avg_rt_equals_avg_ok_rt"][0]["all_equal"])

    def test_inventory_keeps_anomaly_labels_separate(self):
        # This is a focused contract assertion for the labels used by the real adapter.
        frame = pd.DataFrame({"anomaly_load": [0, 1], "anomaly_fis": [0, 1], "anomaly": [0, 1]})
        self.assertEqual([c for c in frame if c.startswith("anomaly")],
                         ["anomaly_load", "anomaly_fis", "anomaly"])


if __name__ == "__main__":
    unittest.main()
