import csv
import io
import json

from fastapi.testclient import TestClient

from aim.main import app
from aim import read_api


def test_ingestion_progress_reports_persisted_points_and_reception_time(monkeypatch):
    class FakeRepository:
        def get_ingestion_progress(self, replay_id, service_id, instance_id):
            assert instance_id == "recommendationservice-1"
            return {
                "replay_run_id": replay_id, "service_id": service_id, "instance_id": instance_id,
                "raw_point_count": 282, "ingest_batch_count": 3,
                "latest_source_timestamp_unix_nano": "1719206040000000000",
                "latest_received_at": "2026-11-12T12:03:00+00:00",
            }

    monkeypatch.setattr(read_api, "Repository", FakeRepository)
    client = TestClient(app)
    response = client.get(
        "/api/v1/replays/4ae6331d-7493-4df7-888c-32dbd2f09244/services/"
        "c2a073d8-2e91-48ba-9e4e-6e8c53759ac1/progress",
        params={"instance_id": "recommendationservice-1"},
    )
    assert response.status_code == 200
    assert response.json()["raw_point_count"] == 282
    assert response.json()["ingest_batch_count"] == 3
    assert response.json()["latest_source_timestamp_unix_nano"] == "1719206040000000000"


def test_raw_export_serializes_persisted_points_and_source_identity(monkeypatch):
    class FakeRepository:
        def get_raw_export(self, replay_id, service_id, instance_id, start, end):
            assert (replay_id, service_id, instance_id, start, end) == (
                "4ae6331d-7493-4df7-888c-32dbd2f09244",
                "c2a073d8-2e91-48ba-9e4e-6e8c53759ac1",
                "recommendationservice-1", 10, 20,
            )
            return {
                "replay_run_id": replay_id, "service_id": service_id,
                "service_name": "recommendationservice", "instance_id": instance_id,
                "from_unix_nano": "10", "to_unix_nano": "20",
                "points": [{
                    "metric_name": "container_cpu_usage_seconds_total", "unit": "s",
                    "value_type": "double", "value": 641.466, "time_unix_nano": "15",
                    "start_time_unix_nano": "", "source_cmdb_id": "recommendationservice-1",
                    "source_file_sha256": "a" * 64, "source_row_ordinal": 42,
                    "metric_series_id": "series-1", "resource_attributes": {"service.name": "recommendationservice"},
                    "scope_attributes": {}, "datapoint_attributes": {"aim.source.row_ordinal": 42},
                }],
            }

    monkeypatch.setattr(read_api, "Repository", FakeRepository)
    client = TestClient(app)
    response = client.get(
        "/api/v1/replays/4ae6331d-7493-4df7-888c-32dbd2f09244/services/"
        "c2a073d8-2e91-48ba-9e4e-6e8c53759ac1/export/raw.csv",
        params={"instance_id": "recommendationservice-1", "from_unix_nano": "10", "to_unix_nano": "20"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=\"aim-raw-points.csv\"" == response.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert rows[0]["replay_run_id"] == "4ae6331d-7493-4df7-888c-32dbd2f09244"
    assert rows[0]["value"] == "641.466"
    assert rows[0]["source_row_ordinal"] == "42"
    assert rows[0]["resource_attributes"] == '{"service.name": "recommendationservice"}'


def test_derived_export_keeps_coverage_reason_and_transform_provenance(monkeypatch):
    class FakeRepository:
        def get_metrics(self, replay_id, service_id, instance_id, transform_id, start, end):
            assert transform_id == "a8dc3d9c-5fd2-4ecf-a538-db9d4c67be77"
            return {
                "replay_run_id": replay_id, "transform_run_id": transform_id,
                "transform_version": "counter-rates-v1", "service_id": service_id,
                "service_name": "recommendationservice", "instance_id": instance_id,
                "metrics": [{
                    "metric_name": "success_latency_mean_ms", "unit": "ms", "value": None,
                    "window_start_unix_nano": "10", "window_end_unix_nano": "20",
                    "coverage_state": "not_applicable", "reason": "no_observed_increment",
                    "provenance": {"formula": "delta(duration)/delta(requests)"},
                }],
            }

    monkeypatch.setattr(read_api, "Repository", FakeRepository)
    client = TestClient(app)
    response = client.get(
        "/api/v1/replays/4ae6331d-7493-4df7-888c-32dbd2f09244/services/"
        "c2a073d8-2e91-48ba-9e4e-6e8c53759ac1/export/derived.csv",
        params={
            "instance_id": "recommendationservice-1",
            "transform_run_id": "a8dc3d9c-5fd2-4ecf-a538-db9d4c67be77",
        },
    )
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert rows[0]["transform_run_id"] == "a8dc3d9c-5fd2-4ecf-a538-db9d4c67be77"
    assert rows[0]["transform_version"] == "counter-rates-v1"
    assert rows[0]["value"] == ""
    assert rows[0]["coverage_state"] == "not_applicable"
    assert rows[0]["reason"] == "no_observed_increment"
    assert rows[0]["provenance"] == '{"formula": "delta(duration)/delta(requests)"}'


def test_derived_export_preserves_selected_60s_version_and_bucket_bounds(monkeypatch):
    transform_id = "a8dc3d9c-5fd2-4ecf-a538-db9d4c67be77"

    class FakeRepository:
        def get_metrics(self, replay_id, service_id, instance_id, selected_transform_id, start, end):
            assert selected_transform_id == transform_id
            assert start == 100
            assert end == 160
            return {
                "replay_run_id": replay_id, "transform_run_id": transform_id,
                "transform_version": "counter-rates-60s-v1", "service_id": service_id,
                "service_name": "recommendationservice", "instance_id": instance_id,
                "metrics": [{
                    "metric_name": "cpu_cores", "unit": "cores", "value": 1.0,
                    "window_start_unix_nano": "100", "window_end_unix_nano": "160",
                    "coverage_state": "complete", "reason": None,
                    "provenance": {
                        "formula": "sum(four delta(cpu_seconds))/60",
                        "input_cadence_seconds": 15,
                    },
                }, {
                    "metric_name": "success_response_rate", "unit": "1/s", "value": None,
                    "window_start_unix_nano": "100", "window_end_unix_nano": "160",
                    "coverage_state": "partial", "reason": "missing_endpoint",
                    "provenance": {
                        "formula": "sum(four delta(grpc.200.0_responses))/60",
                        "source_raw_point_ids": [12, 13, 14],
                        "subwindow_coverage": [
                            {"coverage_state": "complete", "reason": None},
                            {"coverage_state": "partial", "reason": "missing_endpoint"},
                        ],
                    },
                }],
            }

    monkeypatch.setattr(read_api, "Repository", FakeRepository)
    client = TestClient(app)
    response = client.get(
        "/api/v1/replays/4ae6331d-7493-4df7-888c-32dbd2f09244/services/"
        "c2a073d8-2e91-48ba-9e4e-6e8c53759ac1/export/derived.csv",
        params={
            "instance_id": "recommendationservice-1",
            "transform_run_id": transform_id,
            "from_unix_nano": "100",
            "to_unix_nano": "160",
        },
    )
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert rows[0]["transform_run_id"] == transform_id
    assert rows[0]["transform_version"] == "counter-rates-60s-v1"
    assert rows[0]["window_start_unix_nano"] == "100"
    assert rows[0]["window_end_unix_nano"] == "160"
    assert rows[0]["value"] == "1.0"
    assert rows[0]["provenance"] == (
        '{"formula": "sum(four delta(cpu_seconds))/60", "input_cadence_seconds": 15}'
    )
    assert rows[1]["value"] == ""
    assert rows[1]["coverage_state"] == "partial"
    assert rows[1]["reason"] == "missing_endpoint"
    assert json.loads(rows[1]["provenance"])["source_raw_point_ids"] == [12, 13, 14]
