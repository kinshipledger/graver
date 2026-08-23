"""Offline evidence discovery, assessment, and conclusion application services."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from graver.api import _connect, _utc_now_iso
from graver.database import validate_current_database

DISCOVERY_OUTCOMES = (
    "completed",
    "no_results",
    "interrupted",
    "failed",
    "access_restricted",
)
ASSESSMENT_STATES = (
    "new",
    "reviewing",
    "deferred",
    "reopened",
    "ready_for_decision",
)
SIGNAL_CLASSIFICATIONS = (
    "exact",
    "compatible",
    "inferred",
    "missing",
    "conflict",
    "not_comparable",
    "review_required",
)
CONCLUSION_DISPOSITIONS = ("accepted", "rejected", "unresolved", "withdrawn")


class EvidenceError(Exception):
    """Base error for offline evidence-workflow failures."""


class EvidenceInputError(EvidenceError, ValueError):
    """Report an invalid evidence request without presentation details."""


class EvidenceNotFound(EvidenceError):
    """Report that a requested subject, candidate, or assessment does not exist."""


class StaleAssessment(EvidenceError):
    """Prevent one researcher view from overwriting a newer assessment version."""

    def __init__(self, expected_version: int, actual_version: int):
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Assessment version {expected_version} is stale; current version is "
            f"{actual_version}"
        )


def _immutable(connection: sqlite3.Connection, table: str, label: str) -> None:
    for action in ("UPDATE", "DELETE"):
        connection.execute(f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()}
                BEFORE {action} ON {table}
                BEGIN SELECT RAISE(ABORT, '{label} are immutable'); END""")


def create_evidence_schema(connection: sqlite3.Connection) -> None:
    """Create schema-v3 evidence tables without fabricating research records."""
    connection.execute("""CREATE TABLE IF NOT EXISTS candidate_discovery_runs (
        run_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        query_json TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_at TEXT NOT NULL,
        outcome TEXT NOT NULL CHECK (outcome IN (
            'completed', 'no_results', 'interrupted', 'failed', 'access_restricted'
        )),
        error_kind TEXT,
        strategy_version TEXT NOT NULL,
        FOREIGN KEY (subject_id) REFERENCES research_subjects(subject_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS external_candidates (
        candidate_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        provider_profile_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (subject_id, provider, provider_profile_id),
        FOREIGN KEY (subject_id) REFERENCES research_subjects(subject_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS candidate_snapshots (
        snapshot_id TEXT PRIMARY KEY,
        candidate_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        observed_at TEXT NOT NULL,
        profile_url TEXT,
        payload_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        FOREIGN KEY (candidate_id) REFERENCES external_candidates(candidate_id),
        FOREIGN KEY (run_id) REFERENCES candidate_discovery_runs(run_id),
        UNIQUE (run_id, candidate_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS comparison_signals (
        signal_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        candidate_id TEXT NOT NULL,
        snapshot_id TEXT NOT NULL,
        subject_assertion_json TEXT,
        candidate_assertion_json TEXT,
        fact_type TEXT NOT NULL,
        classification TEXT NOT NULL CHECK (classification IN (
            'exact', 'compatible', 'inferred', 'missing', 'conflict',
            'not_comparable', 'review_required'
        )),
        normalized_subject_value TEXT,
        normalized_candidate_value TEXT,
        algorithm_version TEXT NOT NULL,
        ordering_contribution INTEGER NOT NULL DEFAULT 0,
        explanation TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (subject_id) REFERENCES research_subjects(subject_id),
        FOREIGN KEY (candidate_id) REFERENCES external_candidates(candidate_id),
        FOREIGN KEY (snapshot_id) REFERENCES candidate_snapshots(snapshot_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS candidate_assessments (
        candidate_id TEXT PRIMARY KEY,
        state TEXT NOT NULL CHECK (state IN (
            'new', 'reviewing', 'deferred', 'reopened', 'ready_for_decision'
        )),
        version INTEGER NOT NULL CHECK (version >= 1),
        notes TEXT,
        negative_searches_json TEXT NOT NULL DEFAULT '[]',
        unresolved_questions_json TEXT NOT NULL DEFAULT '[]',
        follow_up_condition TEXT,
        review_at TEXT,
        reopens_record_id TEXT,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (candidate_id) REFERENCES external_candidates(candidate_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS candidate_assessment_events (
        event_id TEXT PRIMARY KEY,
        candidate_id TEXT NOT NULL,
        assessment_version INTEGER NOT NULL CHECK (assessment_version >= 1),
        occurred_at TEXT NOT NULL,
        actor TEXT,
        reason TEXT,
        before_json TEXT,
        after_json TEXT NOT NULL,
        FOREIGN KEY (candidate_id) REFERENCES external_candidates(candidate_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS identity_conclusions (
        conclusion_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        candidate_id TEXT NOT NULL,
        disposition TEXT NOT NULL CHECK (disposition IN (
            'accepted', 'rejected', 'unresolved', 'withdrawn'
        )),
        actor TEXT NOT NULL,
        decided_at TEXT NOT NULL,
        analysis TEXT NOT NULL,
        evidence_references_json TEXT NOT NULL,
        material_conflicts_json TEXT NOT NULL,
        supersedes_conclusion_id TEXT,
        FOREIGN KEY (subject_id) REFERENCES research_subjects(subject_id),
        FOREIGN KEY (candidate_id) REFERENCES external_candidates(candidate_id),
        FOREIGN KEY (supersedes_conclusion_id)
            REFERENCES identity_conclusions(conclusion_id)
    )""")
    for table, label in (
        ("candidate_discovery_runs", "candidate discovery runs"),
        ("external_candidates", "external candidates"),
        ("candidate_snapshots", "candidate snapshots"),
        ("comparison_signals", "comparison signals"),
        ("candidate_assessment_events", "candidate assessment events"),
        ("identity_conclusions", "identity conclusions"),
    ):
        _immutable(connection, table, label)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_discovery_runs_subject "
        "ON candidate_discovery_runs(subject_id, started_at, run_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidates_subject "
        "ON external_candidates(subject_id, provider, provider_profile_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidate_snapshots_candidate "
        "ON candidate_snapshots(candidate_id, observed_at, snapshot_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_comparison_signals_candidate "
        "ON comparison_signals(candidate_id, snapshot_id, fact_type, signal_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_assessment_events_candidate "
        "ON candidate_assessment_events(candidate_id, occurred_at, event_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_conclusions_candidate "
        "ON identity_conclusions(candidate_id, decided_at, conclusion_id)"
    )


def _identifier() -> str:
    return str(uuid.uuid4())


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _require_text(value: str, label: str) -> None:
    if not value or not value.strip():
        raise EvidenceInputError(f"{label} is required")


@dataclass(frozen=True)
class CandidateFixture:
    """Represent one curated provider-shaped candidate observation."""

    provider_profile_id: str
    observed_at: str
    assertions: Mapping[str, Any]
    profile_url: Optional[str] = None


@dataclass(frozen=True)
class DiscoveryRequest:
    """Record one bounded, offline candidate-discovery attempt."""

    subject_id: str
    provider: str
    query: Mapping[str, Any]
    started_at: str
    completed_at: str
    strategy_version: str
    candidates: Sequence[CandidateFixture] = ()
    outcome: str = "completed"
    error_kind: Optional[str] = None

    def __post_init__(self) -> None:
        if self.outcome not in DISCOVERY_OUTCOMES:
            raise EvidenceInputError(f"Invalid discovery outcome: {self.outcome}")
        if self.outcome == "no_results" and self.candidates:
            raise EvidenceInputError("A no-results run cannot contain candidates")
        for value, label in (
            (self.subject_id, "Subject identifier"),
            (self.provider, "Provider"),
            (self.started_at, "Start time"),
            (self.completed_at, "Completion time"),
            (self.strategy_version, "Strategy version"),
        ):
            _require_text(value, label)
        profile_ids = [candidate.provider_profile_id for candidate in self.candidates]
        if len(profile_ids) != len(set(profile_ids)):
            raise EvidenceInputError(
                "A discovery run cannot contain the same provider profile twice"
            )


@dataclass(frozen=True)
class CandidateSnapshotRecord:
    """Expose an immutable candidate snapshot without SQLite-shaped values."""

    snapshot_id: str
    candidate_id: str
    provider_profile_id: str
    observed_at: str
    profile_url: Optional[str]
    assertions: Mapping[str, Any]
    content_hash: str


@dataclass(frozen=True)
class DiscoveryResult:
    """Describe a persisted offline discovery run and its immutable snapshots."""

    run_id: str
    subject_id: str
    provider: str
    outcome: str
    snapshots: tuple[CandidateSnapshotRecord, ...]


@dataclass(frozen=True)
class ComparisonSignalInput:
    """Describe one explainable, reproducible comparison signal."""

    fact_type: str
    classification: str
    explanation: str
    subject_assertion: Optional[Mapping[str, Any]] = None
    candidate_assertion: Optional[Mapping[str, Any]] = None
    normalized_subject_value: Optional[str] = None
    normalized_candidate_value: Optional[str] = None
    ordering_contribution: int = 0

    def __post_init__(self) -> None:
        if self.classification not in SIGNAL_CLASSIFICATIONS:
            raise EvidenceInputError(
                f"Invalid signal classification: {self.classification}"
            )
        _require_text(self.fact_type, "Fact type")
        _require_text(self.explanation, "Signal explanation")


@dataclass(frozen=True)
class ComparisonSignalRecord:
    """Expose one immutable comparison signal."""

    signal_id: str
    fact_type: str
    classification: str
    explanation: str
    ordering_contribution: int


@dataclass(frozen=True)
class RankedCandidate:
    """Order one candidate for review without implying confidence or proof."""

    candidate_id: str
    provider_profile_id: str
    review_order: int
    agreement_count: int
    material_conflict_count: int
    unknown_count: int
    algorithm_version: str
    signals: tuple[ComparisonSignalRecord, ...]


@dataclass(frozen=True)
class AssessmentRecord:
    """Represent current candidate-assessment state with a concurrency version."""

    candidate_id: str
    state: str
    version: int
    notes: Optional[str]
    negative_searches: tuple[Mapping[str, Any], ...]
    unresolved_questions: tuple[str, ...]
    follow_up_condition: Optional[str]
    review_at: Optional[str]
    reopens_record_id: Optional[str]
    updated_at: str


@dataclass(frozen=True)
class AssessmentUpdate:
    """Request one meaningful, concurrency-checked assessment transition."""

    candidate_id: str
    expected_version: int
    state: str
    actor: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    negative_searches: Optional[Sequence[Mapping[str, Any]]] = None
    unresolved_questions: Optional[Sequence[str]] = None
    follow_up_condition: Optional[str] = None
    review_at: Optional[str] = None
    reopens_record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.state not in ASSESSMENT_STATES:
            raise EvidenceInputError(f"Invalid assessment state: {self.state}")
        _require_text(self.actor, "Assessment actor")
        if self.state in {"deferred", "reopened"} and not self.reason:
            raise EvidenceInputError(
                f"A reason is required when assessment is {self.state}"
            )
        if self.state == "deferred" and not (
            self.follow_up_condition or self.review_at
        ):
            raise EvidenceInputError(
                "A deferred assessment requires a follow-up condition or review date"
            )
        if self.state == "reopened" and not self.reopens_record_id:
            raise EvidenceInputError(
                "A reopened assessment requires the earlier record identifier"
            )


@dataclass(frozen=True)
class ConclusionRequest:
    """Request one immutable, explicitly reviewed identity conclusion."""

    candidate_id: str
    disposition: str
    actor: str
    analysis: str
    evidence_references: Sequence[Mapping[str, Any]]
    material_conflicts: Sequence[Mapping[str, Any]]
    supersedes_conclusion_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.disposition not in CONCLUSION_DISPOSITIONS:
            raise EvidenceInputError(
                f"Invalid conclusion disposition: {self.disposition}"
            )
        _require_text(self.actor, "Conclusion actor")
        _require_text(self.analysis, "Conclusion analysis")
        if not self.evidence_references:
            raise EvidenceInputError(
                "At least one inspectable evidence reference is required"
            )
        required = {"record_id", "observed_at", "assertions"}
        if any(required - set(reference) for reference in self.evidence_references):
            raise EvidenceInputError(
                "Evidence references require record_id, observed_at, and assertions"
            )
        if self.disposition == "withdrawn" and not self.supersedes_conclusion_id:
            raise EvidenceInputError(
                "A withdrawn conclusion must identify the prior conclusion"
            )


@dataclass(frozen=True)
class ConclusionRecord:
    """Expose one immutable reviewed identity conclusion."""

    conclusion_id: str
    candidate_id: str
    disposition: str
    actor: str
    decided_at: str
    analysis: str
    supersedes_conclusion_id: Optional[str]


@dataclass(frozen=True)
class EvidenceService:
    """Coordinate one database's completely offline evidence workflow."""

    database_name: str

    def record_discovery(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Persist an immutable discovery run and candidate snapshots atomically."""
        validate_current_database(self.database_name)
        run_id = _identifier()
        snapshots = []
        with _connect(self.database_name) as connection:
            if (
                connection.execute(
                    "SELECT 1 FROM research_subjects WHERE subject_id = ?",
                    (request.subject_id,),
                ).fetchone()
                is None
            ):
                raise EvidenceNotFound(
                    f"Research subject {request.subject_id} does not exist"
                )
            connection.execute(
                """INSERT INTO candidate_discovery_runs
                   (run_id, subject_id, provider, query_json, started_at, completed_at,
                    outcome, error_kind, strategy_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    request.subject_id,
                    request.provider,
                    _canonical_json(request.query),
                    request.started_at,
                    request.completed_at,
                    request.outcome,
                    request.error_kind,
                    request.strategy_version,
                ),
            )
            for fixture in request.candidates:
                existing = connection.execute(
                    """SELECT candidate_id FROM external_candidates
                       WHERE subject_id = ? AND provider = ? AND provider_profile_id = ?""",
                    (request.subject_id, request.provider, fixture.provider_profile_id),
                ).fetchone()
                candidate_id = existing[0] if existing else _identifier()
                if existing is None:
                    connection.execute(
                        """INSERT INTO external_candidates
                           (candidate_id, subject_id, provider, provider_profile_id, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            candidate_id,
                            request.subject_id,
                            request.provider,
                            fixture.provider_profile_id,
                            request.completed_at,
                        ),
                    )
                    connection.execute(
                        """INSERT INTO candidate_assessments
                           (candidate_id, state, version, updated_at)
                           VALUES (?, 'new', 1, ?)""",
                        (candidate_id, request.completed_at),
                    )
                    connection.execute(
                        """INSERT INTO candidate_assessment_events
                           (event_id, candidate_id, assessment_version, occurred_at,
                            reason, after_json)
                           VALUES (?, ?, 1, ?, 'candidate_discovered', ?)""",
                        (
                            _identifier(),
                            candidate_id,
                            request.completed_at,
                            _canonical_json({"state": "new", "version": 1}),
                        ),
                    )
                payload = _canonical_json(fixture.assertions)
                content_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                snapshot_id = _identifier()
                connection.execute(
                    """INSERT INTO candidate_snapshots
                       (snapshot_id, candidate_id, run_id, observed_at, profile_url,
                        payload_json, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        snapshot_id,
                        candidate_id,
                        run_id,
                        fixture.observed_at,
                        fixture.profile_url,
                        payload,
                        content_hash,
                    ),
                )
                snapshots.append(
                    CandidateSnapshotRecord(
                        snapshot_id,
                        candidate_id,
                        fixture.provider_profile_id,
                        fixture.observed_at,
                        fixture.profile_url,
                        dict(fixture.assertions),
                        content_hash,
                    )
                )
        return DiscoveryResult(
            run_id,
            request.subject_id,
            request.provider,
            request.outcome,
            tuple(snapshots),
        )

    def record_comparison(
        self,
        snapshot_id: str,
        algorithm_version: str,
        signals: Sequence[ComparisonSignalInput],
    ) -> tuple[ComparisonSignalRecord, ...]:
        """Persist inspectable comparison signals without changing research state."""
        validate_current_database(self.database_name)
        _require_text(algorithm_version, "Algorithm version")
        created_at = _utc_now_iso()
        records = []
        with _connect(self.database_name) as connection:
            row = connection.execute(
                """SELECT c.subject_id, c.candidate_id FROM candidate_snapshots s
                   JOIN external_candidates c ON c.candidate_id = s.candidate_id
                   WHERE s.snapshot_id = ?""",
                (snapshot_id,),
            ).fetchone()
            if row is None:
                raise EvidenceNotFound(
                    f"Candidate snapshot {snapshot_id} does not exist"
                )
            for signal in signals:
                signal_id = _identifier()
                connection.execute(
                    """INSERT INTO comparison_signals
                       (signal_id, subject_id, candidate_id, snapshot_id,
                        subject_assertion_json, candidate_assertion_json, fact_type,
                        classification, normalized_subject_value,
                        normalized_candidate_value, algorithm_version,
                        ordering_contribution, explanation, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        signal_id,
                        row[0],
                        row[1],
                        snapshot_id,
                        (
                            _canonical_json(signal.subject_assertion)
                            if signal.subject_assertion is not None
                            else None
                        ),
                        (
                            _canonical_json(signal.candidate_assertion)
                            if signal.candidate_assertion is not None
                            else None
                        ),
                        signal.fact_type,
                        signal.classification,
                        signal.normalized_subject_value,
                        signal.normalized_candidate_value,
                        algorithm_version,
                        signal.ordering_contribution,
                        signal.explanation,
                        created_at,
                    ),
                )
                records.append(
                    ComparisonSignalRecord(
                        signal_id,
                        signal.fact_type,
                        signal.classification,
                        signal.explanation,
                        signal.ordering_contribution,
                    )
                )
        return tuple(records)

    def list_snapshots(self, candidate_id: str) -> tuple[CandidateSnapshotRecord, ...]:
        """Return every retained candidate snapshot in deterministic order."""
        validate_current_database(self.database_name)
        with _connect(self.database_name) as connection:
            rows = connection.execute(
                """SELECT s.snapshot_id, s.candidate_id, c.provider_profile_id,
                          s.observed_at, s.profile_url, s.payload_json, s.content_hash
                   FROM candidate_snapshots s JOIN external_candidates c
                     ON c.candidate_id=s.candidate_id
                   WHERE s.candidate_id=? ORDER BY s.observed_at, s.snapshot_id""",
                (candidate_id,),
            ).fetchall()
        return tuple(
            CandidateSnapshotRecord(
                row[0], row[1], row[2], row[3], row[4], json.loads(row[5]), row[6]
            )
            for row in rows
        )

    def ranked_candidates(
        self, subject_id: str, algorithm_version: str
    ) -> tuple[RankedCandidate, ...]:
        """Return deterministic review order from the latest candidate snapshots."""
        validate_current_database(self.database_name)
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            candidates = connection.execute(
                """SELECT c.candidate_id, c.provider_profile_id,
                          (SELECT s.snapshot_id FROM candidate_snapshots s
                           WHERE s.candidate_id=c.candidate_id
                           ORDER BY s.observed_at DESC, s.snapshot_id DESC LIMIT 1)
                          AS snapshot_id
                   FROM external_candidates c WHERE c.subject_id = ?
                   ORDER BY c.provider_profile_id""",
                (subject_id,),
            ).fetchall()
            ranked = []
            for candidate in candidates:
                rows = connection.execute(
                    """SELECT signal_id, fact_type, classification, explanation,
                              ordering_contribution FROM comparison_signals
                       WHERE candidate_id = ? AND snapshot_id = ?
                         AND algorithm_version = ? ORDER BY fact_type, signal_id""",
                    (
                        candidate["candidate_id"],
                        candidate["snapshot_id"],
                        algorithm_version,
                    ),
                ).fetchall()
                records = tuple(
                    ComparisonSignalRecord(
                        row["signal_id"],
                        row["fact_type"],
                        row["classification"],
                        row["explanation"],
                        row["ordering_contribution"],
                    )
                    for row in rows
                )
                ranked.append(
                    (
                        sum(item.ordering_contribution for item in records),
                        candidate["provider_profile_id"],
                        candidate["candidate_id"],
                        records,
                    )
                )
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return tuple(
            RankedCandidate(
                candidate_id,
                provider_profile_id,
                order,
                sum(signal.classification == "exact" for signal in records),
                sum(signal.classification == "conflict" for signal in records),
                sum(
                    signal.classification
                    in {"missing", "not_comparable", "review_required"}
                    for signal in records
                ),
                algorithm_version,
                records,
            )
            for order, (_, provider_profile_id, candidate_id, records) in enumerate(
                ranked, start=1
            )
        )

    def update_assessment(self, request: AssessmentUpdate) -> AssessmentRecord:
        """Apply a meaningful assessment update with optimistic concurrency."""
        validate_current_database(self.database_name)
        timestamp = _utc_now_iso()
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            current = connection.execute(
                "SELECT * FROM candidate_assessments WHERE candidate_id = ?",
                (request.candidate_id,),
            ).fetchone()
            if current is None:
                raise EvidenceNotFound(
                    f"Candidate {request.candidate_id} does not exist"
                )
            if current["version"] != request.expected_version:
                raise StaleAssessment(request.expected_version, current["version"])
            negative_searches = (
                json.loads(current["negative_searches_json"])
                if request.negative_searches is None
                else list(request.negative_searches)
            )
            unresolved_questions = (
                json.loads(current["unresolved_questions_json"])
                if request.unresolved_questions is None
                else list(request.unresolved_questions)
            )
            changed = (
                current["state"] != request.state
                or current["notes"] != request.notes
                or json.loads(current["negative_searches_json"]) != negative_searches
                or json.loads(current["unresolved_questions_json"])
                != unresolved_questions
            )
            if not changed:
                return AssessmentRecord(
                    current["candidate_id"],
                    current["state"],
                    current["version"],
                    current["notes"],
                    tuple(json.loads(current["negative_searches_json"])),
                    tuple(json.loads(current["unresolved_questions_json"])),
                    current["follow_up_condition"],
                    current["review_at"],
                    current["reopens_record_id"],
                    current["updated_at"],
                )
            new_version = current["version"] + 1
            connection.execute(
                """UPDATE candidate_assessments SET state=?, version=?, notes=?,
                          negative_searches_json=?, unresolved_questions_json=?,
                          follow_up_condition=?, review_at=?, reopens_record_id=?, updated_at=?
                   WHERE candidate_id=? AND version=?""",
                (
                    request.state,
                    new_version,
                    request.notes,
                    _canonical_json(negative_searches),
                    _canonical_json(unresolved_questions),
                    request.follow_up_condition,
                    request.review_at,
                    request.reopens_record_id,
                    timestamp,
                    request.candidate_id,
                    request.expected_version,
                ),
            )
            before = dict(current)
            after = {
                "candidate_id": request.candidate_id,
                "state": request.state,
                "version": new_version,
                "notes": request.notes,
                "negative_searches": negative_searches,
                "unresolved_questions": unresolved_questions,
                "follow_up_condition": request.follow_up_condition,
                "review_at": request.review_at,
                "reopens_record_id": request.reopens_record_id,
                "updated_at": timestamp,
            }
            connection.execute(
                """INSERT INTO candidate_assessment_events
                   (event_id, candidate_id, assessment_version, occurred_at, actor,
                    reason, before_json, after_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    _identifier(),
                    request.candidate_id,
                    new_version,
                    timestamp,
                    request.actor,
                    request.reason,
                    _canonical_json(before),
                    _canonical_json(after),
                ),
            )
        return AssessmentRecord(
            request.candidate_id,
            request.state,
            new_version,
            request.notes,
            tuple(negative_searches),
            tuple(unresolved_questions),
            request.follow_up_condition,
            request.review_at,
            request.reopens_record_id,
            timestamp,
        )

    def get_assessment(self, candidate_id: str) -> AssessmentRecord:
        """Return current assessment state without exposing persistence rows."""
        validate_current_database(self.database_name)
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM candidate_assessments WHERE candidate_id=?",
                (candidate_id,),
            ).fetchone()
        if row is None:
            raise EvidenceNotFound(f"Candidate {candidate_id} does not exist")
        return AssessmentRecord(
            row["candidate_id"],
            row["state"],
            row["version"],
            row["notes"],
            tuple(json.loads(row["negative_searches_json"])),
            tuple(json.loads(row["unresolved_questions_json"])),
            row["follow_up_condition"],
            row["review_at"],
            row["reopens_record_id"],
            row["updated_at"],
        )

    def assessment_history(self, candidate_id: str) -> tuple[Mapping[str, Any], ...]:
        """Return immutable assessment events with their complete before/after state."""
        validate_current_database(self.database_name)
        with _connect(self.database_name) as connection:
            rows = connection.execute(
                """SELECT event_id, occurred_at, actor, reason, before_json, after_json
                   FROM candidate_assessment_events WHERE candidate_id=?
                   ORDER BY assessment_version""",
                (candidate_id,),
            ).fetchall()
        return tuple(
            {
                "event_id": row[0],
                "occurred_at": row[1],
                "actor": row[2],
                "reason": row[3],
                "before": json.loads(row[4]) if row[4] else None,
                "after": json.loads(row[5]),
            }
            for row in rows
        )

    def record_conclusion(self, request: ConclusionRequest) -> ConclusionRecord:
        """Append a reviewed conclusion without mutating prior decisions."""
        validate_current_database(self.database_name)
        timestamp = _utc_now_iso()
        conclusion_id = _identifier()
        with _connect(self.database_name) as connection:
            row = connection.execute(
                "SELECT subject_id FROM external_candidates WHERE candidate_id = ?",
                (request.candidate_id,),
            ).fetchone()
            if row is None:
                raise EvidenceNotFound(
                    f"Candidate {request.candidate_id} does not exist"
                )
            if request.supersedes_conclusion_id is not None:
                prior = connection.execute(
                    """SELECT candidate_id FROM identity_conclusions
                       WHERE conclusion_id = ?""",
                    (request.supersedes_conclusion_id,),
                ).fetchone()
                if prior is None or prior[0] != request.candidate_id:
                    raise EvidenceInputError(
                        "Superseded conclusion must exist for the same candidate"
                    )
            connection.execute(
                """INSERT INTO identity_conclusions
                   (conclusion_id, subject_id, candidate_id, disposition, actor,
                    decided_at, analysis, evidence_references_json,
                    material_conflicts_json, supersedes_conclusion_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    conclusion_id,
                    row[0],
                    request.candidate_id,
                    request.disposition,
                    request.actor,
                    timestamp,
                    request.analysis,
                    _canonical_json(request.evidence_references),
                    _canonical_json(request.material_conflicts),
                    request.supersedes_conclusion_id,
                ),
            )
        return ConclusionRecord(
            conclusion_id,
            request.candidate_id,
            request.disposition,
            request.actor,
            timestamp,
            request.analysis,
            request.supersedes_conclusion_id,
        )

    def conclusion_history(self, candidate_id: str) -> tuple[ConclusionRecord, ...]:
        """Return immutable conclusion history in deterministic chronological order."""
        validate_current_database(self.database_name)
        with _connect(self.database_name) as connection:
            rows = connection.execute(
                """SELECT conclusion_id, candidate_id, disposition, actor, decided_at,
                          analysis, supersedes_conclusion_id FROM identity_conclusions
                   WHERE candidate_id=? ORDER BY decided_at, conclusion_id""",
                (candidate_id,),
            ).fetchall()
        return tuple(ConclusionRecord(*row) for row in rows)
