"""Typed application services for graver clients.

This module is the supported pre-1.0 import boundary for application code. It
contains no CLI, terminal-rendering, Qt, SQLite connection, or third-party HTTP
types. The future workspace façade will compose these same request, result, error,
and service objects rather than replacing their domain meaning.

Examples:
    Create a database and query its research queue without global configuration::

        from graver.application import ResearchService, ResearchTaskQuery, create_database

        database = create_database("research.db")
        service = ResearchService(str(database))
        tasks = service.query_tasks(ResearchTaskQuery(limit=10))
"""

from graver.database import (
    DatabaseInitializationError,
    DatabaseInspectionError,
    DatabaseLifecycleError,
    DatabaseUpgradeError,
    create_database,
    inspect_database,
    upgrade_database,
    validate_current_database,
)
from graver.evidence import (
    AssessmentRecord,
    AssessmentUpdate,
    CandidateInput,
    CandidateSnapshotRecord,
    ComparisonSignalInput,
    ComparisonSignalRecord,
    ConclusionRecord,
    ConclusionRequest,
    DiscoveryRequest,
    DiscoveryResult,
    EvidenceError,
    EvidenceInputError,
    EvidenceNotFound,
    EvidenceService,
    RankedCandidate,
    SourceObservationInput,
    SourceObservationRecord,
    StaleAssessment,
)
from graver.research import (
    EnrichmentAliasBlocked,
    EnrichmentFailed,
    EnrichmentNotApproved,
    EnrichmentRedirected,
    EnrichmentRedirectInvalid,
    ResearchEnrichmentRequest,
    ResearchEnrichmentResult,
    ResearchInputError,
    ResearchQueueRequest,
    ResearchQueueResult,
    ResearchService,
    ResearchTaskDetail,
    ResearchTaskQuery,
    ResearchTaskRecord,
    ResearchTaskSummary,
    ResearchTaskUpdate,
)

__all__ = (
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
    "SourceObservationInput",
    "SourceObservationRecord",
    "StaleAssessment",
    "create_database",
    "inspect_database",
    "upgrade_database",
    "validate_current_database",
)
