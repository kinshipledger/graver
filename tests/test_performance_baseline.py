"""Contract tests for the non-blocking performance baseline."""

import pytest

from benchmarks.performance_baseline import run_baseline

pytestmark = pytest.mark.integration


def test_performance_report_uses_disposable_generated_data(tmp_path) -> None:
    """The harness reports stable fields without external services or user data."""
    report = run_baseline((3,), repetitions=2, directory=tmp_path)

    assert report["schema_version"] == 1
    assert report["method"]["latency"].endswith("not a CI gate")
    assert report["datasets"][0]["records"] == 3
    assert report["datasets"][0]["database_bytes"] > 0
    assert set(report["datasets"][0]["operations"]) == {
        "workspace_open",
        "work_list_50",
        "work_show",
        "work_update",
    }
    assert all(
        measurement["median_ms"] >= 0
        for measurement in report["datasets"][0]["operations"].values()
    )
