import csv
import json

import pytest

from aim.dataset import DISPLAY_END, DISPLAY_START, SERIES, SOURCE_START, load_cut, load_ground_truth
from aim.replay import build_request, verify_persisted


@pytest.fixture
def external_dataset(tmp_path):
    base = tmp_path / "Case-1" / "Case-1"
    for spec in SERIES:
        path = base / spec.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(("timestamp", "cmdb_id", "kpi_name", "value"))
            for offset, timestamp in enumerate(range(SOURCE_START, DISPLAY_END + 15, 15)):
                writer.writerow((timestamp, "unrelated-instance", spec.metric_name, 999))
                writer.writerow((timestamp, spec.cmdb_id, spec.metric_name, 100 + offset))
    path = base / "groundtruth/groundtruth.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"timestamp": [1719206280], "service": ["recommendationservice"], "cmdb_id": ["recommendationservice-1"], "failure_type": ["cpu"], "duration": [780]}))
    return tmp_path


def test_replayer_preserves_original_samples_and_global_source_ordinals(external_dataset):
    cut = load_cut(external_dataset)
    request = build_request(cut, "00000000-0000-0000-0000-000000000001")
    assert len(request.resource_metrics) == 3
    for resource, series in zip(request.resource_metrics, cut.series):
        metric = resource.scope_metrics[0].metrics[0]
        assert metric.name == series.spec.metric_name
        assert metric.unit == series.spec.unit
        assert len(metric.sum.data_points) == 94
        for offset, point in enumerate(metric.sum.data_points):
            assert point.as_double == 100 + offset
            assert point.time_unix_nano == (SOURCE_START + offset * 15) * 1_000_000_000
            assert point.start_time_unix_nano == 0
            attributes = {attribute.key: attribute.value for attribute in point.attributes}
            assert attributes["aim.source.row_ordinal"].int_value == (offset + 1) * 2
        assert not any(name in metric.name for name in ("cpu_cores", "success_response_rate", "success_latency_mean_ms"))


def test_replayer_can_build_ordered_otlp_chunks(external_dataset):
    cut = load_cut(external_dataset)
    request = build_request(cut, "00000000-0000-0000-0000-000000000001", 8, 16)
    assert len(request.resource_metrics) == 3
    for resource, series in zip(request.resource_metrics, cut.series):
        points = resource.scope_metrics[0].metrics[0].sum.data_points
        assert len(points) == 8
        assert points[0].time_unix_nano == series.points[8].timestamp * 1_000_000_000
        assert points[-1].time_unix_nano == series.points[15].timestamp * 1_000_000_000


def test_replayer_rejects_chunks_that_break_shared_time_grid(external_dataset):
    cut = load_cut(external_dataset)
    from dataclasses import replace

    broken_series = replace(cut.series[1], points=cut.series[1].points[:-1])
    broken_cut = replace(cut, series=(cut.series[0], broken_series, cut.series[2]))
    with pytest.raises(ValueError, match="share the same timestamp sequence"):
        build_request(broken_cut, "00000000-0000-0000-0000-000000000001", 0, 8)


def test_ground_truth_is_a_distinct_operation_and_type(external_dataset):
    digest, events = load_ground_truth(external_dataset)
    assert len(digest) == 64
    assert events[0]["event_type"] == "injected_fault"
    assert events[0]["source_event_ordinal"] == 1
    assert events[0]["end_unix_nano"] - events[0]["start_unix_nano"] == 780 * 1_000_000_000


def test_changed_source_grid_is_rejected(external_dataset):
    path = external_dataset / "Case-1/Case-1" / SERIES[0].relative_path
    content = path.read_text()
    # Removing a selected endpoint is not repaired by interpolation.
    path.write_text("\n".join(line for line in content.splitlines() if not line.startswith(f"{DISPLAY_START},{SERIES[0].cmdb_id},")) + "\n")
    with pytest.raises(ValueError, match="Source cut changed"):
        load_cut(external_dataset)


def test_raw_verifier_rejects_a_changed_value(external_dataset):
    cut = load_cut(external_dataset)
    raw = [{"metric_name": series.spec.metric_name, "source_cmdb_id": series.spec.cmdb_id, "time_unix_nano": point.timestamp * 1_000_000_000, "source_file_sha256": series.file_sha256, "source_row_ordinal": point.row_ordinal, "value": point.value} for series in cut.series for point in series.points]
    assert verify_persisted(cut, raw)["verified_points"] == 282
    raw[0]["value"] += 1
    with pytest.raises(ValueError, match="1 different values"):
        verify_persisted(cut, raw)
