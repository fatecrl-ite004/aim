from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from google.rpc.status_pb2 import Status
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceResponse

from aim.dataset import DatasetCut, SERIES, SourcePoint, SourceSeries
from aim.main import app
from aim.repository import Repository, _typed_number


def _manifest() -> dict:
    files = [
        {"role": role, "relative_path": f"metric/{role}.csv", "sha256": digest, "size_bytes": 1}
        for role, digest in (("cpu", "a" * 64), ("requests", "b" * 64), ("duration", "c" * 64), ("ground_truth", "d" * 64))
    ]
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"files": files, "manifest_sha256": hashlib.sha256(canonical).hexdigest()}


def _int_cut(value: int, replay_id: str | None = None) -> DatasetCut:
    spec = SERIES[0]
    point = SourcePoint(timestamp=1_719_205_965, value=value, row_ordinal=1)
    series = SourceSeries(spec=spec, file_sha256="a" * 64, points=(point,))
    return DatasetCut(source_manifest=_manifest(), series=(series,))


def test_int64_typed_value_conversion_does_not_round_through_float():
    value = 9_007_199_254_740_993

    result = _typed_number("int", value, None)

    assert result == value
    assert isinstance(result, int)


def test_otlp_receiver_round_trips_int64_and_rejects_conflicting_retry():
    if not os.getenv("AIM_DATABASE_URL"):
        pytest.skip("AIM_DATABASE_URL is not configured")
    repository = Repository()
    try:
        if not repository.check_ready():
            pytest.skip("AIM PostgreSQL schema is not ready")
    except Exception as error:
        pytest.skip(f"AIM PostgreSQL is unavailable: {type(error).__name__}")

    value = 9_007_199_254_740_993
    cut = _int_cut(value)
    ts = cut.series[0].points[0].timestamp * 1_000_000_000
    replay = repository.create_replay({
        "dataset": "aiopsarena", "dataset_case": "Case-1",
        "service_name": "recommendationservice", "instance_id": "recommendationservice-1",
        "display_start_unix_nano": str(ts), "display_end_unix_nano": str(ts + 1_000_000_000),
        "raw_start_unix_nano": str(ts), "raw_end_unix_nano": str(ts + 1_000_000_000),
        "source_manifest": cut.source_manifest, "replayer_version": "test-replayer",
        "mapping_version": "test-mapping",
    })
    replay_id = replay["replay_run_id"]
    client = TestClient(app)
    try:
        payload = cut.series[0]
        from aim.replay import build_request

        first = build_request(cut, replay_id)
        datapoint = first.resource_metrics[0].scope_metrics[0].metrics[0].sum.data_points[0]
        datapoint.as_int = value
        encoded = first.SerializeToString(deterministic=True)
        accepted = client.post("/v1/metrics", content=encoded, headers={"Content-Type": "application/x-protobuf"})
        assert accepted.status_code == 200
        assert accepted.headers["content-type"].startswith("application/x-protobuf")
        assert not ExportMetricsServiceResponse.FromString(accepted.content).HasField("partial_success")
        persisted = repository.get_raw_points(replay_id)
        assert len(persisted) == 1
        assert persisted[0]["value"] == value
        assert isinstance(persisted[0]["value"], int)

        conflicting = build_request(cut, replay_id)
        conflicting_point = conflicting.resource_metrics[0].scope_metrics[0].metrics[0].sum.data_points[0]
        conflicting_point.as_int = value + 1
        rejected = client.post(
            "/v1/metrics",
            content=conflicting.SerializeToString(deterministic=True),
            headers={"Content-Type": "application/x-protobuf"},
        )
        assert rejected.status_code == 409
        assert rejected.headers["content-type"].startswith("application/x-protobuf")
        assert Status.FromString(rejected.content).code == 6
        assert repository.get_raw_points(replay_id)[0]["value"] == value
    finally:
        from aim.db import connection

        with connection() as conn:
            conn.execute("DELETE FROM replay_run WHERE replay_run_id=%s", (replay_id,))
