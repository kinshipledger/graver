"""Measure repeatable offline application-service performance baselines."""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import statistics
import sys
import tempfile
import time
import tracemalloc
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from graver.application import (
    MemorialSummaryBatch,
    MemorialSummaryInput,
    MemorialSummarySearchRequest,
    ResearchQueueRequest,
    ResearchTaskQuery,
    ResearchTaskUpdate,
    create_database,
    open_workspace,
)


def _summary(memorial_id: int) -> MemorialSummaryInput:
    """Build one deterministic fictional summary without external data."""
    return MemorialSummaryInput(
        memorial_id=memorial_id,
        findagrave_url=f"https://example.invalid/memorial/{memorial_id}",
        prefix="",
        name=f"Performance Fixture {memorial_id:09d}",
        suffix="",
        nickname="",
        maiden_name="",
        famous=False,
        veteran=False,
        birth="1900",
        death="1980",
        memorial_type="Burial",
        cemetery_id=1,
        burial_place="Fictional Performance Cemetery",
        plot=f"Section {memorial_id % 100}",
    )


def _timed(call: Callable[[], Any], repetitions: int = 1) -> dict[str, Any]:
    """Measure latency samples and peak traced Python allocation."""
    samples = []
    peak_bytes = 0
    for _ in range(repetitions):
        gc.collect()
        tracemalloc.start()
        started = time.perf_counter()
        call()
        samples.append((time.perf_counter() - started) * 1000)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_bytes = max(peak_bytes, peak)
    ordered = sorted(samples)
    percentile_index = min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))
    return {
        "samples": len(samples),
        "median_ms": round(statistics.median(samples), 3),
        "p95_ms": round(ordered[percentile_index], 3),
        "peak_python_bytes": peak_bytes,
    }


def _measure_dataset(directory: Path, records: int, repetitions: int) -> dict[str, Any]:
    """Create one disposable dataset and measure public workspace operations."""
    database = create_database(str(directory / f"baseline-{records}.db"))
    workspace = open_workspace(database)
    summaries = tuple(_summary(memorial_id) for memorial_id in range(1, records + 1))

    acquisition = _timed(
        lambda: workspace.acquisition.search(
            MemorialSummarySearchRequest(max_results=records),
            acquire=lambda _request: MemorialSummaryBatch(
                summaries, f"fixture:performance:{records}"
            ),
        )
    )
    queue = _timed(lambda: workspace.work.queue(ResearchQueueRequest()))
    middle_id = max(1, records // 2)
    operations = {
        "workspace_open": _timed(lambda: open_workspace(database), repetitions),
        "work_list_50": _timed(
            lambda: workspace.work.list(ResearchTaskQuery(limit=50)), repetitions
        ),
        "work_show": _timed(lambda: workspace.work.show(middle_id), repetitions),
    }
    detail = workspace.work.show(middle_id)
    operations["work_update"] = _timed(
        lambda: workspace.work.update(
            ResearchTaskUpdate(
                memorial_id=middle_id,
                expected_version=detail.task.version,
                priority=detail.task.priority + 1,
            )
        )
    )
    return {
        "records": records,
        "database_bytes": database.stat().st_size,
        "setup": {"summary_acquisition": acquisition, "queue_all": queue},
        "operations": operations,
    }


def run_baseline(
    sizes: Sequence[int], repetitions: int, directory: Path
) -> dict[str, Any]:
    """Return a versioned performance report for deterministic generated data."""
    if not sizes or any(size < 1 for size in sizes):
        raise ValueError("Every performance dataset size must be positive")
    if repetitions < 1:
        raise ValueError("Performance repetitions must be positive")
    return {
        "schema_version": 1,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "revision": os.environ.get("GITHUB_SHA", "local"),
        },
        "method": {
            "repetitions": repetitions,
            "network": "disabled by design; no provider adapter is invoked",
            "memory": "peak Python allocations traced per operation",
            "latency": "wall-clock milliseconds; informational, not a CI gate",
        },
        "datasets": [_measure_dataset(directory, size, repetitions) for size in sizes],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure graver's offline workspace performance."
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=(100, 10_000),
        help="Generated memorial/task counts (default: 100 10000).",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=7,
        help="Repeated read-operation samples per dataset (default: 7).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path in addition to standard output.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the baseline in an isolated temporary directory."""
    arguments = _parse_args()
    with tempfile.TemporaryDirectory(prefix="graver-performance-") as temporary:
        report = run_baseline(arguments.sizes, arguments.repetitions, Path(temporary))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    sys.stdout.write(rendered)
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
