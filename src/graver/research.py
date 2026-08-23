"""Internal subject-oriented research task repositories and services."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

import graver.api as legacy_api
from graver.api import (
    RESEARCH_TASK_STATUSES,
    NotFound,
    ResearchTaskNotFound,
    _connect,
    _ensure_subject_for_memorial,
    _initialize_database,
    _record_task_event,
    _resolve_alias,
    _row_to_dict,
    _sources_for_canonical,
)
from graver.constants import MEMORIAL_CANONICAL_URL_FORMAT
from graver.database import validate_current_database

__all__ = (
    "EnrichmentAliasBlocked",
    "EnrichmentFailed",
    "EnrichmentNotApproved",
    "EnrichmentRedirectInvalid",
    "EnrichmentRedirected",
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
)


class ResearchInputError(ValueError):
    """Report an invalid application-service request without presentation details."""


class EnrichmentNotApproved(Exception):
    """Report that a task has not been approved for full acquisition."""


class EnrichmentAliasBlocked(Exception):
    """Report that known redirect evidence blocks acquisition of a memorial."""

    def __init__(self, memorial_id: int, canonical_id: int, path: tuple[int, ...]):
        self.memorial_id = memorial_id
        self.canonical_id = canonical_id
        self.path = path
        super().__init__(f"Memorial {memorial_id} redirects to {canonical_id}")


class EnrichmentRedirected(Exception):
    """Report newly observed redirect evidence recorded during acquisition."""

    def __init__(self, memorial_id: int, target_memorial_id: int):
        self.memorial_id = memorial_id
        self.target_memorial_id = target_memorial_id
        super().__init__(f"Memorial {memorial_id} redirects to {target_memorial_id}")


class EnrichmentFailed(Exception):
    """Report a recorded acquisition failure using safe researcher-facing context."""

    def __init__(self, memorial_id: int, cause: Exception):
        self.memorial_id = memorial_id
        self.error_type = type(cause).__name__
        self.message = " ".join(str(cause).split())
        super().__init__(self.message)


class EnrichmentRedirectInvalid(EnrichmentFailed):
    """Report malformed or mismatched redirect evidence from acquisition."""


@dataclass(frozen=True)
class ResearchTaskQuery:
    """Select an ordered page of subject-owned research tasks."""

    status: Optional[str] = None
    cemetery_id: Optional[int] = None
    limit: int = 20

    def __post_init__(self) -> None:
        if self.status is not None and self.status not in RESEARCH_TASK_STATUSES:
            raise ResearchInputError(f"Invalid task status: {self.status}")
        if self.limit < 1:
            raise ResearchInputError("Limit must be at least 1")


@dataclass(frozen=True)
class ResearchTaskUpdate:
    """Describe an explicit partial update to one research task."""

    memorial_id: int
    status: Optional[str] = None
    priority: Optional[int] = None
    owner: Optional[str] = None
    review_note: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status is not None and self.status not in RESEARCH_TASK_STATUSES:
            raise ResearchInputError(f"Invalid task status: {self.status}")
        if not self.changes:
            raise ResearchInputError("At least one task change is required")

    @property
    def changes(self) -> dict[str, Any]:
        """Return only fields explicitly supplied by the caller."""
        return {
            key: value
            for key, value in {
                "status": self.status,
                "priority": self.priority,
                "owner": self.owner,
                "review_note": self.review_note,
            }.items()
            if value is not None
        }


@dataclass(frozen=True)
class ResearchQueueRequest:
    """Describe a request to queue acquired memorials for research."""

    cemetery_id: Optional[int] = None
    priority: int = 0


@dataclass(frozen=True)
class ResearchQueueResult:
    """Summarize idempotent research-task creation."""

    created: int
    existing: int

    def to_compatibility_tuple(self) -> tuple[int, int]:
        """Project the pre-1.0 queue return contract."""
        return self.created, self.existing


@dataclass(frozen=True)
class ResearchEnrichmentRequest:
    """Request retrieval of exactly one approved memorial."""

    memorial_id: int


@dataclass(frozen=True)
class ResearchEnrichmentResult:
    """Describe successful persistence of one full memorial observation."""

    memorial_id: int
    status: str
    full_observed_at: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ResearchEnrichmentResult":
        """Create a typed result from the compatibility persistence boundary."""
        return cls(
            memorial_id=value["memorial_id"],
            status=value["status"],
            full_observed_at=value["full_observed_at"],
        )

    def to_compatibility_dict(self) -> dict[str, Any]:
        """Project the existing command/API dictionary contract."""
        return {
            "memorial_id": self.memorial_id,
            "status": self.status,
            "full_observed_at": self.full_observed_at,
        }


@dataclass(frozen=True)
class ResearchTaskSummary:
    """Represent one ordered research-queue entry for application clients."""

    memorial_id: int
    name: Optional[str]
    birth: Optional[str]
    death: Optional[str]
    cemetery_id: Optional[int]
    detail_level: Optional[str]
    status: str
    priority: int
    owner: Optional[str]
    last_activity_at: str
    alias_target_id: Optional[int]
    alias_status: Optional[str]
    alias_canonical_id: int
    alias_path: tuple[int, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ResearchTaskSummary":
        """Create a typed summary from one repository projection."""
        return cls(
            memorial_id=value["memorial_id"],
            name=value["name"],
            birth=value["birth"],
            death=value["death"],
            cemetery_id=value["cemetery_id"],
            detail_level=value["detail_level"],
            status=value["status"],
            priority=value["priority"],
            owner=value["owner"],
            last_activity_at=value["last_activity_at"],
            alias_target_id=value["alias_target_id"],
            alias_status=value["alias_status"],
            alias_canonical_id=value["alias_canonical_id"],
            alias_path=tuple(value["alias_path"]),
        )

    def to_compatibility_dict(self) -> dict[str, Any]:
        """Project the pre-1.0 memorial-shaped dictionary contract."""
        return {
            "memorial_id": self.memorial_id,
            "name": self.name,
            "birth": self.birth,
            "death": self.death,
            "cemetery_id": self.cemetery_id,
            "detail_level": self.detail_level,
            "status": self.status,
            "priority": self.priority,
            "owner": self.owner,
            "last_activity_at": self.last_activity_at,
            "alias_target_id": self.alias_target_id,
            "alias_status": self.alias_status,
            "alias_canonical_id": self.alias_canonical_id,
            "alias_path": list(self.alias_path),
        }


@dataclass(frozen=True)
class ResearchTaskRecord:
    """Represent current subject-owned task state and its memorial lookup."""

    subject_id: str
    memorial_id: int
    status: str
    priority: int
    owner: Optional[str]
    created_at: str
    updated_at: str
    last_activity_at: str
    review_note: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row, memorial_id: int) -> "ResearchTaskRecord":
        """Create a typed task record from one repository row."""
        return cls(
            subject_id=row["subject_id"],
            memorial_id=memorial_id,
            status=row["status"],
            priority=row["priority"],
            owner=row["owner"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_activity_at=row["last_activity_at"],
            review_note=row["review_note"],
        )

    def to_compatibility_dict(self) -> dict[str, Any]:
        """Project task state without exposing the transitional subject UUID."""
        return {
            "memorial_id": self.memorial_id,
            "status": self.status,
            "priority": self.priority,
            "owner": self.owner,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_activity_at": self.last_activity_at,
            "review_note": self.review_note,
        }


@dataclass(frozen=True)
class ResearchTaskDetail:
    """Aggregate task state and source context for one memorial lookup."""

    task: ResearchTaskRecord
    grave: Mapping[str, Any]
    cemetery: Optional[Mapping[str, Any]]
    observations: tuple[Mapping[str, Any], ...]
    alias: Mapping[str, Any]

    def to_compatibility_dict(self) -> dict[str, Any]:
        """Project the existing command/API dictionary without shared mutability."""
        return {
            "task": self.task.to_compatibility_dict(),
            "grave": dict(self.grave),
            "cemetery": dict(self.cemetery) if self.cemetery is not None else None,
            "observations": [dict(item) for item in self.observations],
            "alias": dict(self.alias),
        }


class _ResearchTaskRepository:
    """Keep subject-task persistence details behind the application service."""

    @staticmethod
    def list_tasks(
        connection: sqlite3.Connection,
        status: Optional[str],
        cemetery_id: Optional[int],
        limit: int,
    ) -> list[sqlite3.Row]:
        clauses = []
        parameters = {"status": status, "cemetery_id": cemetery_id, "limit": limit}
        if status is not None:
            clauses.append("t.status = :status")
        if cemetery_id is not None:
            clauses.append(
                "EXISTS (SELECT 1 FROM subject_memorials filter_sm "
                "JOIN graves filter_g ON filter_g.memorial_id = filter_sm.memorial_id "
                "WHERE filter_sm.subject_id = t.subject_id "
                "AND filter_g.cemetery_id = :cemetery_id)"
            )
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return connection.execute(
            f"""SELECT g.memorial_id, g.name, g.birth, g.death,
                       g.cemetery_id, g.detail_level, t.status, t.priority,
                       t.owner, t.last_activity_at,
                       a.target_memorial_id AS alias_target_id,
                       a.status AS alias_status
                FROM research_tasks AS t
                JOIN (
                    SELECT subject_id, MIN(memorial_id) AS memorial_id
                    FROM subject_memorials GROUP BY subject_id
                ) AS display_sm ON display_sm.subject_id = t.subject_id
                JOIN graves AS g ON g.memorial_id = display_sm.memorial_id
                LEFT JOIN memorial_aliases AS a
                  ON a.source_memorial_id = g.memorial_id AND a.status = 'active'
                {where}
                ORDER BY t.priority DESC, t.last_activity_at ASC,
                         g.memorial_id ASC
                LIMIT :limit""",
            parameters,
        ).fetchall()

    @staticmethod
    def grave(
        connection: sqlite3.Connection, memorial_id: int
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM graves WHERE memorial_id = ?", (memorial_id,)
        ).fetchone()

    @staticmethod
    def task_for_memorial(
        connection: sqlite3.Connection, memorial_id: int
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            """SELECT t.* FROM research_tasks AS t
               JOIN subject_memorials AS sm ON sm.subject_id = t.subject_id
               WHERE sm.memorial_id = ?""",
            (memorial_id,),
        ).fetchone()

    @staticmethod
    def task_for_subject(
        connection: sqlite3.Connection, subject_id: str
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM research_tasks WHERE subject_id = ?", (subject_id,)
        ).fetchone()

    @staticmethod
    def cemetery(
        connection: sqlite3.Connection, cemetery_id: int
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM cemeteries WHERE cemetery_id = ?", (cemetery_id,)
        ).fetchone()

    @staticmethod
    def observations(
        connection: sqlite3.Connection, memorial_id: int
    ) -> list[sqlite3.Row]:
        return connection.execute(
            """SELECT observation_id, memorial_id, cemetery_id,
                      acquisition_level, observed_at, fetch_outcome,
                      parser_version, payload_json
               FROM memorial_observations WHERE memorial_id = ?
               ORDER BY observed_at ASC, observation_id ASC""",
            (memorial_id,),
        ).fetchall()

    @staticmethod
    def subject_has_task_for_memorial(
        connection: sqlite3.Connection, memorial_id: int
    ) -> bool:
        return (
            connection.execute(
                """SELECT 1 FROM research_tasks AS t
                   JOIN subject_memorials AS sm ON sm.subject_id = t.subject_id
                   WHERE sm.memorial_id = ?""",
                (memorial_id,),
            ).fetchone()
            is not None
        )

    @staticmethod
    def update_task(
        connection: sqlite3.Connection, subject_id: str, changes: dict
    ) -> None:
        assignments = ", ".join(f"{key} = :{key}" for key in changes)
        connection.execute(
            f"UPDATE research_tasks SET {assignments} WHERE subject_id = :subject_id",
            {**changes, "subject_id": subject_id},
        )

    @staticmethod
    def memorial_ids(
        connection: sqlite3.Connection, cemetery_id: Optional[int]
    ) -> list[int]:
        if cemetery_id is None:
            rows = connection.execute(
                "SELECT memorial_id FROM graves ORDER BY memorial_id"
            )
        else:
            rows = connection.execute(
                """SELECT memorial_id FROM graves
                   WHERE cemetery_id = ? ORDER BY memorial_id""",
                (cemetery_id,),
            )
        return [row[0] for row in rows]

    @staticmethod
    def create_task(
        connection: sqlite3.Connection,
        subject_id: str,
        priority: int,
        timestamp: str,
    ) -> bool:
        cursor = connection.execute(
            """INSERT INTO research_tasks (
                   subject_id, status, priority, created_at, updated_at,
                   last_activity_at
               ) VALUES (?, 'unprocessed', ?, ?, ?, ?)
               ON CONFLICT(subject_id) DO NOTHING""",
            (subject_id, priority, timestamp, timestamp, timestamp),
        )
        return bool(cursor.rowcount)


def _memorial_id_from_url(url: str) -> Optional[int]:
    """Extract a Find a Grave memorial identifier from redirect evidence."""
    match = re.search(r"/memorial/(\d+)(?:/|$)", url)
    return int(match.group(1)) if match else None


@dataclass(frozen=True)
class ResearchService:
    """Coordinate subject-owned research work for one explicit database."""

    database_name: str

    def resolve_alias(self, memorial_id: int) -> dict:
        """Resolve platform redirect evidence without changing subject membership."""
        return legacy_api.resolve_memorial_alias(self.database_name, memorial_id)

    def list_tasks(
        self,
        status: Optional[str] = None,
        cemetery_id: Optional[int] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Return the transitional dictionary projection for existing callers."""
        return [
            task.to_compatibility_dict()
            for task in self.query_tasks(ResearchTaskQuery(status, cemetery_id, limit))
        ]

    def query_tasks(
        self, query: ResearchTaskQuery = ResearchTaskQuery()
    ) -> tuple[ResearchTaskSummary, ...]:
        """Return typed research tasks in deterministic queue order."""
        validate_current_database(self.database_name)
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            results = []
            for row in _ResearchTaskRepository.list_tasks(
                connection, query.status, query.cemetery_id, query.limit
            ):
                item = _row_to_dict(row)
                resolution = _resolve_alias(connection, item["memorial_id"])
                item["alias_canonical_id"] = resolution["canonical_memorial_id"]
                item["alias_path"] = resolution["path"]
                results.append(ResearchTaskSummary.from_mapping(item))
        return tuple(results)

    def show_task(self, memorial_id: int) -> dict:
        """Return the transitional dictionary projection for existing callers."""
        return self.get_task(memorial_id).to_compatibility_dict()

    def get_task(self, memorial_id: int) -> ResearchTaskDetail:
        """Return typed task and source context resolved by memorial ID."""
        validate_current_database(self.database_name)
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            grave = _ResearchTaskRepository.grave(connection, memorial_id)
            if grave is None:
                raise NotFound(f"Memorial {memorial_id} does not exist")
            task = _ResearchTaskRepository.task_for_memorial(connection, memorial_id)
            if task is None:
                raise ResearchTaskNotFound(
                    f"Research task {memorial_id} does not exist"
                )
            cemetery = (
                _ResearchTaskRepository.cemetery(connection, grave["cemetery_id"])
                if grave["cemetery_id"] is not None
                else None
            )
            observations = _ResearchTaskRepository.observations(connection, memorial_id)
            resolution = _resolve_alias(connection, memorial_id)
            canonical_id = resolution["canonical_memorial_id"]
            canonical_grave = (
                _ResearchTaskRepository.grave(connection, canonical_id) is not None
            )
            canonical_task = _ResearchTaskRepository.subject_has_task_for_memorial(
                connection, canonical_id
            )
            related_sources = [
                source_id
                for source_id in _sources_for_canonical(connection, canonical_id)
                if source_id != memorial_id
            ]
        observation_dicts = []
        for row in observations:
            observation = _row_to_dict(row)
            observation["payload"] = json.loads(observation.pop("payload_json"))
            observation_dicts.append(observation)
        return ResearchTaskDetail(
            task=ResearchTaskRecord.from_row(task, memorial_id),
            grave=_row_to_dict(grave),
            cemetery=_row_to_dict(cemetery) if cemetery is not None else None,
            observations=tuple(observation_dicts),
            alias={
                "is_active_source": len(resolution["path"]) > 1,
                **resolution,
                "canonical_target_exists": canonical_grave,
                "canonical_target_has_task": canonical_task,
                "other_active_sources": related_sources,
            },
        )

    def update_task(
        self,
        memorial_id: int,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        owner: Optional[str] = None,
        review_note: Optional[str] = None,
    ) -> dict:
        """Return the transitional dictionary projection for existing callers."""
        return self.apply_task_update(
            ResearchTaskUpdate(
                memorial_id,
                status=status,
                priority=priority,
                owner=owner,
                review_note=review_note,
            )
        ).to_compatibility_dict()

    def apply_task_update(self, command: ResearchTaskUpdate) -> ResearchTaskRecord:
        """Apply one validated partial update and record meaningful change history."""
        validate_current_database(self.database_name)
        requested = command.changes
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            current = _ResearchTaskRepository.task_for_memorial(
                connection, command.memorial_id
            )
            if current is None:
                raise ResearchTaskNotFound(
                    f"Research task {command.memorial_id} does not exist"
                )
            changed = {
                key: value for key, value in requested.items() if current[key] != value
            }
            if changed:
                timestamp = legacy_api._utc_now_iso()
                before = _row_to_dict(current)
                changed["updated_at"] = timestamp
                if "status" in changed or "review_note" in changed:
                    changed["last_activity_at"] = timestamp
                _ResearchTaskRepository.update_task(
                    connection, current["subject_id"], changed
                )
                result = _ResearchTaskRepository.task_for_subject(
                    connection, current["subject_id"]
                )
                if result is None:
                    raise ResearchTaskNotFound(
                        f"Research task {command.memorial_id} disappeared during update"
                    )
                _record_task_event(
                    connection,
                    current["subject_id"],
                    "task_updated",
                    timestamp,
                    before,
                    _row_to_dict(result),
                    reason="researcher_update",
                )
            else:
                result = current
        return ResearchTaskRecord.from_row(result, command.memorial_id)

    def queue_memorials(
        self, cemetery_id: Optional[int] = None, priority: int = 0
    ) -> tuple[int, int]:
        """Return the transitional queue tuple for existing callers."""
        return self.queue_research(
            ResearchQueueRequest(cemetery_id, priority)
        ).to_compatibility_tuple()

    def queue_research(self, command: ResearchQueueRequest) -> ResearchQueueResult:
        """Create subject-owned tasks for acquired memorials idempotently."""
        _initialize_database(self.database_name)
        timestamp = legacy_api._utc_now_iso()
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            subject_ids = [
                _ensure_subject_for_memorial(connection, memorial_id, timestamp)
                for memorial_id in _ResearchTaskRepository.memorial_ids(
                    connection, command.cemetery_id
                )
            ]
            eligible_subjects = list(dict.fromkeys(subject_ids))
            created = 0
            for subject_id in eligible_subjects:
                if not _ResearchTaskRepository.create_task(
                    connection, subject_id, command.priority, timestamp
                ):
                    continue
                created += 1
                task = _ResearchTaskRepository.task_for_subject(connection, subject_id)
                _record_task_event(
                    connection,
                    subject_id,
                    "task_created",
                    timestamp,
                    None,
                    _row_to_dict(task),
                    reason="queued_for_research",
                )
        return ResearchQueueResult(created, len(eligible_subjects) - created)

    def enrich_memorial(
        self,
        command: ResearchEnrichmentRequest,
        acquire: Optional[Callable[[str], object]] = None,
    ) -> ResearchEnrichmentResult:
        """Acquire and persist exactly one approved memorial with fail-closed safety."""
        current = self.get_task(command.memorial_id)
        if current.task.status != "ready_for_full_scrape":
            raise EnrichmentNotApproved(
                f"Task {command.memorial_id} is not ready_for_full_scrape"
            )
        resolution = self.resolve_alias(command.memorial_id)
        path = tuple(resolution["path"])
        if len(path) > 1:
            raise EnrichmentAliasBlocked(
                command.memorial_id,
                resolution["canonical_memorial_id"],
                path,
            )
        attempted_url = current.grave["findagrave_url"] or (
            MEMORIAL_CANONICAL_URL_FORMAT.format(command.memorial_id)
        )
        acquire_memorial = acquire or legacy_api.Memorial.parse
        try:
            memorial = acquire_memorial(attempted_url)
        except legacy_api.MemorialMergedException as merged:
            source_id = _memorial_id_from_url(merged.old_url)
            target_id = _memorial_id_from_url(merged.new_url)
            if source_id != command.memorial_id or target_id is None:
                self.record_enrichment_failure(
                    command.memorial_id, attempted_url, merged
                )
                raise EnrichmentRedirectInvalid(command.memorial_id, merged) from merged
            self.record_redirect_failure(
                command.memorial_id,
                target_id,
                merged.old_url,
                merged.new_url,
                merged,
            )
            raise EnrichmentRedirected(command.memorial_id, target_id) from merged
        except Exception as ex:
            self.record_enrichment_failure(command.memorial_id, attempted_url, ex)
            raise EnrichmentFailed(command.memorial_id, ex) from ex
        return ResearchEnrichmentResult.from_mapping(
            self.complete_enrichment(command.memorial_id, memorial)
        )

    def complete_enrichment(self, memorial_id: int, memorial: object) -> dict:
        """Persist one successful approved memorial acquisition atomically."""
        return legacy_api.save_completed_task_scrape(
            self.database_name, memorial_id, memorial
        )

    def record_enrichment_failure(
        self, memorial_id: int, attempted_url: str, exception: Exception
    ) -> str:
        """Record one failed approved acquisition without advancing its task."""
        return legacy_api.record_failed_task_scrape(
            self.database_name, memorial_id, attempted_url, exception
        )

    def record_redirect_failure(
        self,
        memorial_id: int,
        target_memorial_id: int,
        source_url: str,
        target_url: str,
        exception: Exception,
    ) -> str:
        """Record redirect evidence discovered during an approved acquisition."""
        return legacy_api.record_merged_task_scrape(
            self.database_name,
            memorial_id,
            target_memorial_id,
            source_url,
            target_url,
            exception,
        )
