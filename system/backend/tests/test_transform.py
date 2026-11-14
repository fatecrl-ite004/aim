from __future__ import annotations

import pytest

from aim.dataset import DISPLAY_START, INSTANCE, NANO, SERVICE, SERIES
from aim.transform import derive_observations, derive_observations_60s, run_transform, run_transform_60s


def source_points(cpu=(10, 40), requests=(100, 160), duration=(200, 320)):
    points = []
    for series_id, (spec, values) in enumerate(zip(SERIES, (cpu, requests, duration)), 1):
        for offset, value in enumerate(values):
            points.append({
                "id": len(points) + 1, "series_id": str(series_id), "metric_name": spec.metric_name,
                "unit": spec.unit, "service_name": SERVICE, "instance_id": INSTANCE,
                "source_cmdb_id": spec.cmdb_id, "time_unix_nano": (DISPLAY_START + offset * 15) * NANO,
                "start_time_unix_nano": None, "value": value,
            })
    return points


def source_points_60s(
    cpu=(0, 15, 30, 45, 60),
    requests=(0, 15, 30, 45, 60),
    duration=(0, 30, 60, 90, 120),
):
    points = []
    for series_id, (spec, values) in enumerate(zip(SERIES, (cpu, requests, duration)), 1):
        for offset, value in enumerate(values):
            points.append({
                "id": len(points) + 1, "series_id": str(series_id), "metric_name": spec.metric_name,
                "unit": spec.unit, "service_name": SERVICE, "instance_id": INSTANCE,
                "source_cmdb_id": spec.cmdb_id, "time_unix_nano": (DISPLAY_START + offset * 15) * NANO,
                "start_time_unix_nano": None, "value": value,
            })
    return points


def derive(points):
    rows, summary = derive_observations(points, start_unix_nano=DISPLAY_START * NANO, end_unix_nano=(DISPLAY_START + 15) * NANO)
    return {row["metric_name"]: row for row in rows}, summary


def derive_60s(points, end_offset=60):
    rows, summary = derive_observations_60s(
        points,
        start_unix_nano=DISPLAY_START * NANO,
        end_unix_nano=(DISPLAY_START + end_offset) * NANO,
    )
    return {row["metric_name"]: row for row in rows}, summary


def test_derives_only_supported_statistics_with_units_and_provenance():
    rows, summary = derive(source_points())
    assert rows["cpu_cores"]["value"] == 2
    assert rows["cpu_cores"]["unit"] == "cores"
    assert rows["success_response_rate"]["value"] == 4
    assert rows["success_latency_mean_ms"]["value"] == 2
    assert rows["success_latency_mean_ms"]["source_raw_point_ids"] == [3, 4, 5, 6]
    assert summary["numeric_derived_points"] == 3


def test_zero_observed_traffic_has_a_rate_but_no_latency():
    rows, summary = derive(source_points(requests=(100, 100), duration=(200, 200)))
    assert rows["success_response_rate"]["value"] == 0
    assert rows["success_response_rate"]["coverage_state"] == "complete"
    assert rows["success_latency_mean_ms"]["value"] is None
    assert rows["success_latency_mean_ms"]["coverage_state"] == "not_applicable"
    assert rows["success_latency_mean_ms"]["reason"] == "no_observed_increment"
    assert summary["numeric_derived_points"] == 2


def test_counter_decrease_never_becomes_zero_or_negative_feature():
    rows, _ = derive(source_points(cpu=(40, 10), requests=(160, 100)))
    for name in ("cpu_cores", "success_response_rate", "success_latency_mean_ms"):
        assert rows[name]["value"] is None
        assert rows[name]["coverage_state"] == "invalid"
        assert rows[name]["reason"] == "counter_decreased"


def test_missing_endpoint_is_partial_without_imputation():
    points = source_points()
    points.pop(1)
    rows, _ = derive(points)
    assert rows["cpu_cores"]["value"] is None
    assert rows["cpu_cores"]["coverage_state"] == "partial"
    assert rows["success_response_rate"]["coverage_state"] == "complete"


def test_duplicate_timestamp_is_explicitly_invalid():
    points = source_points()
    points.append({**points[0], "id": 99})
    rows, _ = derive(points)
    assert rows["cpu_cores"]["value"] is None
    assert rows["cpu_cores"]["reason"] == "duplicate_timestamp"


def test_latency_requires_matching_api_identity():
    points = source_points()
    for point in points:
        if point["metric_name"] == SERIES[2].metric_name:
            point["source_cmdb_id"] = "another-edge"
    rows, _ = derive(points)
    assert rows["success_latency_mean_ms"]["value"] is None
    assert rows["success_latency_mean_ms"]["reason"] == "api_identity_mismatch"


def test_duration_without_responses_is_invalid():
    rows, _ = derive(source_points(requests=(100, 100), duration=(200, 320)))
    assert rows["success_latency_mean_ms"]["value"] is None
    assert rows["success_latency_mean_ms"]["reason"] == "duration_without_responses"


def test_latency_requires_shared_resource_dimensions():
    points = source_points()
    for point in points:
        point["resource_attributes"] = {"zone": "a" if point["metric_name"] == SERIES[1].metric_name else "b"}
    rows, _ = derive(points)
    assert rows["success_latency_mean_ms"]["value"] is None
    assert rows["success_latency_mean_ms"]["reason"] == "api_identity_mismatch"


def test_latency_requires_shared_scope():
    points = source_points()
    for point in points:
        point["scope_name"] = "scope-a" if point["metric_name"] == SERIES[1].metric_name else "scope-b"
    rows, _ = derive(points)
    assert rows["success_latency_mean_ms"]["value"] is None
    assert rows["success_latency_mean_ms"]["reason"] == "api_identity_mismatch"


def test_integer_counter_delta_keeps_single_increment_above_double_precision():
    rows, _ = derive(source_points(requests=(9_007_199_254_740_992, 9_007_199_254_740_993), duration=(100, 103)))
    assert rows["success_response_rate"]["value"] == 1 / 15
    assert rows["success_latency_mean_ms"]["value"] == 3


def test_warmup_interval_stays_outside_display():
    points = source_points()
    for point in list(points[::2]):
        points.append({**point, "id": point["id"] + 100, "time_unix_nano": (DISPLAY_START - 15) * NANO, "value": 0})
    rows, summary = derive(points)
    assert summary["visible_windows"] == 1
    assert len(rows) == 3
    assert all(row["window_start_unix_nano"] == DISPLAY_START * NANO for row in rows.values())


def test_60s_transform_aggregates_four_complete_subwindows_and_keeps_units():
    rows, summary = derive_60s(source_points_60s())
    assert rows["cpu_cores"]["value"] == 1
    assert rows["success_response_rate"]["value"] == 1
    assert rows["success_latency_mean_ms"]["value"] == 2
    assert all(row["coverage_state"] == "complete" for row in rows.values())
    assert all(row["window_start_unix_nano"] == DISPLAY_START * NANO for row in rows.values())
    assert all(row["window_end_unix_nano"] == (DISPLAY_START + 60) * NANO for row in rows.values())
    assert summary["window_seconds"] == 60
    assert summary["input_cadence_seconds"] == 15
    assert summary["visible_windows"] == 1
    assert summary["coverage_rows"] == 3
    assert summary["numeric_derived_points"] == 3


def test_60s_reset_in_any_subwindow_invalidates_the_aggregate_without_clamping():
    rows, _ = derive_60s(source_points_60s(requests=(100, 115, 110, 125, 140)))
    assert rows["success_response_rate"]["value"] is None
    assert rows["success_response_rate"]["coverage_state"] == "invalid"
    assert rows["success_response_rate"]["reason"] == "counter_decreased"
    assert rows["success_response_rate"]["provenance"]["source_raw_point_ids"]
    assert rows["success_latency_mean_ms"]["coverage_state"] == "invalid"
    request_states = rows["success_response_rate"]["provenance"]["subwindow_coverage"]
    assert [item["coverage_state"] for item in request_states] == ["complete", "invalid", "complete", "complete"]


def test_60s_missing_subwindow_is_partial_without_imputation():
    points = source_points_60s()
    missing_time = (DISPLAY_START + 30) * NANO
    points = [
        point for point in points
        if not (point["metric_name"] == SERIES[0].metric_name and int(point["time_unix_nano"]) == missing_time)
    ]
    rows, _ = derive_60s(points)
    assert rows["cpu_cores"]["value"] is None
    assert rows["cpu_cores"]["coverage_state"] == "partial"
    assert rows["cpu_cores"]["reason"] == "missing_endpoint"
    assert rows["cpu_cores"]["provenance"]["source_raw_point_ids"]


def test_60s_no_observed_increment_requires_four_valid_request_and_duration_deltas():
    rows, _ = derive_60s(source_points_60s(
        requests=(100, 100, 100, 100, 100),
        duration=(200, 200, 200, 200, 200),
    ))
    assert rows["success_response_rate"]["value"] == 0
    assert rows["success_response_rate"]["coverage_state"] == "complete"
    assert rows["success_response_rate"]["reason"] == "no_observed_increment"
    assert rows["success_latency_mean_ms"]["value"] is None
    assert rows["success_latency_mean_ms"]["coverage_state"] == "not_applicable"
    assert rows["success_latency_mean_ms"]["reason"] == "no_observed_increment"


def test_60s_zero_request_rate_does_not_claim_no_observed_when_duration_is_incomplete():
    points = source_points_60s(requests=(100, 100, 100, 100, 100))
    missing_time = (DISPLAY_START + 30) * NANO
    points = [
        point for point in points
        if not (point["metric_name"] == SERIES[2].metric_name and int(point["time_unix_nano"]) == missing_time)
    ]
    rows, _ = derive_60s(points)
    assert rows["success_response_rate"]["value"] == 0
    assert rows["success_response_rate"]["coverage_state"] == "complete"
    assert rows["success_response_rate"]["reason"] is None
    assert rows["success_latency_mean_ms"]["coverage_state"] == "partial"


def test_60s_counter_sums_preserve_integer_deltas_above_double_precision():
    base = 9_007_199_254_740_992
    rows, _ = derive_60s(source_points_60s(
        requests=(base, base + 1, base + 2, base + 3, base + 4),
        duration=(0, 1, 2, 3, 4),
    ))
    assert rows["success_response_rate"]["value"] == 4 / 60
    assert rows["success_latency_mean_ms"]["value"] == 1


class MemoryRepository:
    def __init__(self, raw_points, display_end_offset=30):
        self.raw_points = raw_points
        self.display_end_offset = display_end_offset
        self.config = None
        self.rows = None
        self.status = None
        self.version = None

    def get_replay(self, replay_id):
        return {
            "replay_run_id": replay_id,
            "display_start_unix_nano": DISPLAY_START * NANO,
            "display_end_unix_nano": (DISPLAY_START + self.display_end_offset) * NANO,
            "service_name": SERVICE,
            "instance_id": INSTANCE,
        }

    def get_raw_points(self, replay_id):
        return self.raw_points

    def start_transform_run(self, replay_id, version, config):
        self.config = config
        self.version = version
        return "transform-1"

    def write_transform_results(self, transform_id, rows):
        self.rows = rows

    def finish_transform_run(self, transform_id, status, summary=None, error=None):
        self.status = status


def test_progressive_transform_uses_only_the_persisted_prefix_through_watermark():
    points = source_points()
    for point in list(points):
        points.append({
            **point,
            "id": point["id"] + 100,
            "time_unix_nano": (DISPLAY_START + 30) * NANO,
            "value": point["value"] + 30,
        })
    repository = MemoryRepository(points)

    result = run_transform(repository, "replay-1", until_unix_nano=(DISPLAY_START + 15) * NANO)

    assert result["status"] == "complete"
    assert result["summary"]["input_raw_points"] == 6
    assert result["summary"]["visible_windows"] == 1
    assert result["summary"]["visible_end_unix_nano"] == str((DISPLAY_START + 15) * NANO)
    assert len(repository.rows) == 3
    assert all(row["window_end_unix_nano"] <= (DISPLAY_START + 15) * NANO for row in repository.rows)
    assert repository.config["display_end_unix_nano"] == str((DISPLAY_START + 15) * NANO)


def test_progressive_transform_rejects_watermark_beyond_persisted_points():
    repository = MemoryRepository(source_points())
    with pytest.raises(ValueError, match="exceeds the latest persisted source timestamp"):
        run_transform(repository, "replay-1", until_unix_nano=(DISPLAY_START + 30) * NANO)


def test_progressive_60s_transform_persists_only_complete_buckets_and_versioned_config():
    repository = MemoryRepository(source_points_60s(), display_end_offset=60)
    result = run_transform_60s(repository, "replay-1", until_unix_nano=(DISPLAY_START + 60) * NANO)
    assert result["version"] == "counter-rates-60s-v1"
    assert repository.version == "counter-rates-60s-v1"
    assert repository.config["window_seconds"] == 60
    assert repository.config["input_cadence_seconds"] == 15
    assert repository.config["bucket_alignment"] == "display_start"
    assert repository.config["display_end_unix_nano"] == str((DISPLAY_START + 60) * NANO)
    assert result["summary"]["visible_windows"] == 1
    assert result["summary"]["coverage_rows"] == 3
    assert len(repository.rows) == 3


def test_progressive_60s_transform_skips_a_trailing_partial_bucket():
    points = [
        point for point in source_points_60s()
        if int(point["time_unix_nano"]) <= (DISPLAY_START + 45) * NANO
    ]
    repository = MemoryRepository(points, display_end_offset=60)
    with pytest.raises(ValueError, match="No complete 60-second bucket"):
        run_transform_60s(repository, "replay-1", until_unix_nano=(DISPLAY_START + 45) * NANO)
