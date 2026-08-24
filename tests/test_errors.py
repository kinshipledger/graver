"""Contract tests for presentation-neutral application failures."""

from types import MappingProxyType

import pytest

from graver.application import (
    ApplicationError,
    CancellationRequested,
    DatabaseBusy,
    EvidenceInputError,
    StaleAssessment,
    StaleResearchTask,
    WorkItemNotFound,
)


@pytest.mark.parametrize(
    ("error", "code", "context"),
    [
        (
            WorkItemNotFound(1075),
            "resource_not_found",
            {"memorial_id": 1075},
        ),
        (
            StaleResearchTask(1075, 2, 3),
            "stale_data",
            {"memorial_id": 1075, "expected_version": 2, "actual_version": 3},
        ),
        (
            StaleAssessment(4, 5),
            "stale_data",
            {"expected_version": 4, "actual_version": 5},
        ),
        (
            CancellationRequested("enrich_memorial", "validation"),
            "operation_cancelled",
            {"operation": "enrich_memorial", "stage": "validation"},
        ),
        (
            DatabaseBusy("/research/graver.db", "list research work"),
            "database_busy",
            {
                "database": "/research/graver.db",
                "operation": "list research work",
            },
        ),
    ],
)
def test_supported_failures_have_stable_safe_immutable_fields(error, code, context):
    """Adapters can route failures without parsing presentation text."""
    assert isinstance(error, ApplicationError)
    assert error.code == code
    assert error.summary == str(error)
    assert error.context == context
    assert isinstance(error.context, MappingProxyType)
    with pytest.raises(TypeError):
        error.context["changed"] = True


def test_application_error_normalizes_summary_without_changing_legacy_type() -> None:
    """Existing domain catches remain valid while presentation fields stay safe."""
    error = EvidenceInputError(" Invalid\n  comparison input ")

    assert isinstance(error, ValueError)
    assert error.code == "invalid_request"
    assert error.summary == "Invalid comparison input"
    assert error.context == {}
