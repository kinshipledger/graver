"""Typed application services for graver clients.

This module is the supported pre-1.0 import boundary for application code. It
contains no CLI, terminal-rendering, Qt, SQLite connection, or third-party HTTP
types. The initial synchronous workspace façade composes these same request, result,
error, and service objects rather than replacing their domain meaning.

Examples:
    Open a database and query its research queue without global configuration::

        from graver.application import ResearchTaskQuery, open_workspace

        workspace = open_workspace("research.db")
        tasks = workspace.work.list(ResearchTaskQuery(limit=10))
"""

from graver.database import (
    DatabaseInitializationError,
    DatabaseInspectionError,
    DatabaseLifecycleError,
    DatabaseUpgradeError,
    DatabaseUpgradeResult,
    SchemaInspection,
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
from graver.workspace import (
    GraverWorkspace,
    WorkItemNotFound,
    WorkspaceDatabase,
    WorkspaceWork,
    open_workspace,
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
)
