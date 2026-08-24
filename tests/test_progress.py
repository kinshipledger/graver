"""Contract tests for toolkit-neutral progress and cancellation."""

import threading

import pytest

from graver.application import (
    CancellationRequested,
    CancellationToken,
    ProgressEvent,
)


def test_cancellation_token_is_idempotent_and_safe_across_threads() -> None:
    token = CancellationToken()

    thread = threading.Thread(target=token.cancel)
    thread.start()
    thread.join()
    token.cancel()

    assert token.cancelled is True
    with pytest.raises(CancellationRequested) as cancelled:
        token.raise_if_cancelled("test_operation", "safe_boundary")
    assert cancelled.value.operation == "test_operation"
    assert cancelled.value.stage == "safe_boundary"
    assert str(cancelled.value) == "test_operation was cancelled during safe_boundary"


@pytest.mark.parametrize(
    "event_factory, message",
    [
        (
            lambda: ProgressEvent("", "stage", 0),
            "Progress operation and stage are required",
        ),
        (
            lambda: ProgressEvent("operation", "stage", -1),
            "completed count cannot be negative",
        ),
        (
            lambda: ProgressEvent("operation", "stage", 2, 1),
            "total cannot be less than completed count",
        ),
    ],
)
def test_progress_events_reject_invalid_counts(event_factory, message) -> None:
    with pytest.raises(ValueError, match=message):
        event_factory()


def test_progress_event_is_immutable_and_supports_unknown_totals() -> None:
    event = ProgressEvent("search", "page", 3, message="Page complete")

    assert event.total is None
    with pytest.raises(AttributeError):
        event.completed = 4
