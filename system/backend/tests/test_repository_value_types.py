from contextlib import contextmanager
from datetime import datetime, timezone

from aim import repository as repository_module
from aim.repository import Repository, _typed_number


REPLAY_ID = "4ae6331d-7493-4df7-888c-32dbd2f09244"


def test_raw_int64_value_preserves_precision_beyond_javascript_safe_integer():
    exact_value = 9_007_199_254_740_993

    result = _typed_number("int", exact_value, None)

    assert result == exact_value
    assert isinstance(result, int)


def test_raw_double_value_stays_a_float():
    result = _typed_number("double", None, 0.125)

    assert result == 0.125
    assert isinstance(result, float)


def _transform_row(transform_id, version, status, completed_at):
    return {
        "transform_run_id": transform_id,
        "replay_run_id": REPLAY_ID,
        "version": version,
        "config": {},
        "status": status,
        "summary": {},
        "error": None,
        "created_at": datetime(2026, 11, 11, tzinfo=timezone.utc),
        "completed_at": completed_at,
    }


def _list_transforms_with_rows(monkeypatch, transform_rows):
    class Result:
        def __init__(self, row=None, rows=None):
            self.row = row
            self.rows = rows or []

        def fetchone(self):
            return self.row

        def fetchall(self):
            return self.rows

    class FakeConnection:
        def execute(self, query, params=()):
            if "FROM replay_run" in query:
                return Result(row={"replay_run_id": REPLAY_ID})
            if "FROM transform_run" in query:
                return Result(rows=transform_rows)
            raise AssertionError(f"Unexpected query: {query}")

    @contextmanager
    def fake_connection(_dsn):
        yield FakeConnection()

    monkeypatch.setattr(repository_module, "connection", fake_connection)
    return Repository(dsn="unused").list_transforms(REPLAY_ID)


def test_list_transforms_prefers_latest_completed_60s_run_without_reordering_history(monkeypatch):
    latest = datetime(2026, 11, 11, 12, 3, tzinfo=timezone.utc)
    aggregate_latest = datetime(2026, 11, 11, 12, 2, tzinfo=timezone.utc)
    aggregate_older = datetime(2026, 11, 11, 12, 1, tzinfo=timezone.utc)
    rows = [
        _transform_row("faithful-newest", "counter-rates-v1", "complete", latest),
        _transform_row("aggregate-latest", "counter-rates-60s-v1", "complete", aggregate_latest),
        _transform_row("aggregate-older", "counter-rates-60s-v1", "complete", aggregate_older),
        _transform_row("aggregate-failed", "counter-rates-60s-v1", "failed", None),
    ]

    result = _list_transforms_with_rows(monkeypatch, rows)

    assert result["default_transform_run_id"] == "aggregate-latest"
    assert [item["transform_run_id"] for item in result["transforms"]] == [
        "faithful-newest", "aggregate-latest", "aggregate-older", "aggregate-failed",
    ]


def test_list_transforms_falls_back_to_latest_completed_run_without_completed_60s(monkeypatch):
    latest = datetime(2026, 11, 11, 12, 3, tzinfo=timezone.utc)
    older = datetime(2026, 11, 11, 12, 1, tzinfo=timezone.utc)
    rows = [
        _transform_row("faithful-newest", "counter-rates-v1", "complete", latest),
        _transform_row("aggregate-failed", "counter-rates-60s-v1", "failed", None),
        _transform_row("faithful-older", "counter-rates-v1", "complete", older),
    ]

    result = _list_transforms_with_rows(monkeypatch, rows)

    assert result["default_transform_run_id"] == "faithful-newest"
    assert [item["transform_run_id"] for item in result["transforms"]] == [
        "faithful-newest", "aggregate-failed", "faithful-older",
    ]
