"""Protect graver's documented typed application import boundary."""

import inspect

import graver.application as application

EXPECTED_PUBLIC_NAMES = {
    "AssessmentRecord",
    "AssessmentUpdate",
    "CandidateInput",
    "CandidateSnapshotRecord",
    "ComparisonSignalInput",
    "ComparisonSignalRecord",
    "ConclusionRecord",
    "ConclusionRequest",
    "DatabaseInitializationError",
    "DatabaseInspectionError",
    "DatabaseLifecycleError",
    "DatabaseUpgradeError",
    "DatabaseUpgradeResult",
    "DiscoveryRequest",
    "DiscoveryResult",
    "EnrichmentAliasBlocked",
    "EnrichmentFailed",
    "EnrichmentNotApproved",
    "EnrichmentRedirectInvalid",
    "EnrichmentRedirected",
    "EvidenceError",
    "EvidenceInputError",
    "EvidenceNotFound",
    "EvidenceService",
    "GraverWorkspace",
    "RankedCandidate",
    "ResearchEnrichmentRequest",
    "ResearchEnrichmentResult",
    "ResearchInputError",
    "ResearchQueueRequest",
    "ResearchQueueResult",
    "ResearchService",
    "ResearchTaskDetail",
    "ResearchTaskQuery",
    "ResearchTaskRecord",
    "ResearchTaskSummary",
    "ResearchTaskUpdate",
    "SchemaInspection",
    "SourceObservationInput",
    "SourceObservationRecord",
    "StaleAssessment",
    "WorkItemNotFound",
    "WorkspaceDatabase",
    "WorkspaceWork",
    "create_database",
    "inspect_database",
    "open_workspace",
    "upgrade_database",
    "validate_current_database",
}


def test_application_exports_are_explicit_and_documented():
    """Every supported symbol is intentional, importable, and explained."""
    assert set(application.__all__) == EXPECTED_PUBLIC_NAMES
    assert len(application.__all__) == len(set(application.__all__))
    for name in application.__all__:
        value = getattr(application, name)
        assert inspect.getdoc(value), f"Public symbol {name} needs a useful docstring"


def test_application_boundary_excludes_adapter_and_storage_types():
    """Public imports must not expose implementation frameworks or SQL handles."""
    forbidden = {
        "Driver",
        "HttpTransport",
        "RequestsTransport",
        "TransportResponse",
        "app",
        "click",
        "sqlite3",
        "typer",
    }
    assert forbidden.isdisjoint(application.__all__)


def test_application_star_import_matches_all():
    """Wildcard import behavior is deterministic for documentation tooling."""
    namespace: dict[str, object] = {}
    exec("from graver.application import *", {}, namespace)
    assert set(namespace) == EXPECTED_PUBLIC_NAMES
