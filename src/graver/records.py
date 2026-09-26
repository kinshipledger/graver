# SPDX-FileCopyrightText: 2026 Larry McQueary
# SPDX-License-Identifier: MIT

"""Typed stored-memorial reads and immediate foreground acquisition."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

import graver.api as legacy_api
from graver.constants import MEMORIAL_CANONICAL_URL_FORMAT
from graver.database import validate_current_database
from graver.errors import ApplicationError
from graver.progress import (
    CancellationRequested,
    CancellationToken,
    ProgressEvent,
    ProgressObserver,
)
from graver.research import DisplayedRelationshipInput, MemorialDetailInput

__all__ = (
    "CemeteryRecord",
    "MemorialAliasRecord",
    "MemorialFetchAliasBlocked",
    "MemorialFetchFailed",
    "MemorialFetchInvalid",
    "MemorialFetchRedirectInvalid",
    "MemorialFetchRedirected",
    "MemorialFetchRequest",
    "MemorialFetchResult",
    "MemorialFieldChange",
    "MemorialObservationRecord",
    "MemorialRecord",
    "MemorialRecordDetail",
    "MemorialRecordInputError",
    "MemorialRecordNotFound",
    "MemorialRecordQuery",
    "MemorialRecordService",
    "MemorialRecordSnapshot",
    "MemorialRecordSummary",
    "MemorialRedirectInput",
)


_MEMORIAL_FIELDS = (
    "memorial_id",
    "findagrave_url",
    "prefix",
    "name",
    "suffix",
    "nickname",
    "maiden_name",
    "original_name",
    "famous",
    "veteran",
    "birth",
    "birth_place",
    "death",
    "death_place",
    "memorial_type",
    "cemetery_id",
    "burial_place",
    "plot",
    "coords",
    "has_bio",
    "date_added",
)


class MemorialRecordInputError(ApplicationError, ValueError):
    """Report an invalid stored-record request."""

    code = "invalid_request"


class MemorialRecordNotFound(ApplicationError, LookupError):
    """Report that a stored memorial record does not exist."""

    code = "resource_not_found"

    def __init__(self, memorial_id: int):
        self.memorial_id = memorial_id
        ApplicationError.__init__(
            self,
            f"Memorial record {memorial_id} does not exist",
            context={"memorial_id": memorial_id},
        )


class MemorialFetchAliasBlocked(ApplicationError):
    """Report that a known redirect blocks acquisition of the old identifier."""

    code = "acquisition_blocked"

    def __init__(self, memorial_id: int, canonical_id: int, path: tuple[int, ...]):
        self.memorial_id = memorial_id
        self.canonical_id = canonical_id
        self.path = path
        super().__init__(
            f"Memorial {memorial_id} redirects to {canonical_id}",
            context={
                "memorial_id": memorial_id,
                "canonical_id": canonical_id,
                "path": path,
            },
        )


class MemorialFetchFailed(ApplicationError):
    """Report a recorded foreground acquisition failure."""

    code = "acquisition_failed"

    def __init__(self, memorial_id: int, cause: Exception):
        self.memorial_id = memorial_id
        self.error_type = type(cause).__name__
        self.message = " ".join(str(cause).split())
        super().__init__(
            self.message,
            context={
                "memorial_id": memorial_id,
                "error_type": self.error_type,
            },
        )


class MemorialFetchInvalid(MemorialFetchFailed):
    """Report acquired content that does not match the requested record."""

    code = "acquisition_result_invalid"


class MemorialFetchRedirected(ApplicationError):
    """Report newly recorded provider redirect information."""

    code = "acquisition_redirected"

    def __init__(self, memorial_id: int, target_memorial_id: int):
        self.memorial_id = memorial_id
        self.target_memorial_id = target_memorial_id
        super().__init__(
            f"Memorial {memorial_id} redirects to {target_memorial_id}",
            context={
                "memorial_id": memorial_id,
                "target_memorial_id": target_memorial_id,
            },
        )


class MemorialFetchRedirectInvalid(MemorialFetchFailed):
    """Report redirect information that does not describe the requested record."""

    code = "acquisition_redirect_invalid"


@dataclass(frozen=True)
class MemorialRedirectInput:
    """Carry a redirect observed by an acquisition adapter."""

    source_url: str
    target_url: str


@dataclass(frozen=True)
class MemorialRecordQuery:
    """Select an ordered page of stored memorial records."""

    cemetery_id: Optional[int] = None
    limit: int = 20

    def __post_init__(self) -> None:
        if self.cemetery_id is not None and self.cemetery_id < 1:
            raise MemorialRecordInputError("Cemetery ID must be positive")
        if self.limit < 1:
            raise MemorialRecordInputError("Limit must be at least 1")


@dataclass(frozen=True)
class MemorialRecordSummary:
    """Represent one stored memorial without workflow state."""

    memorial_id: int
    name: Optional[str]
    birth: Optional[str]
    death: Optional[str]
    cemetery_id: Optional[int]
    burial_place: Optional[str]
    detail_level: Optional[str]
    findagrave_url: Optional[str]
    saved_version_count: int
    last_observed_at: Optional[str]


@dataclass(frozen=True)
class MemorialRecord:
    """Represent the current stored values for one memorial."""

    memorial_id: int
    findagrave_url: Optional[str]
    prefix: Optional[str]
    name: Optional[str]
    suffix: Optional[str]
    nickname: Optional[str]
    maiden_name: Optional[str]
    original_name: Optional[str]
    famous: Optional[bool]
    veteran: Optional[bool]
    birth: Optional[str]
    birth_place: Optional[str]
    death: Optional[str]
    death_place: Optional[str]
    memorial_type: Optional[str]
    cemetery_id: Optional[int]
    burial_place: Optional[str]
    plot: Optional[str]
    coords: Optional[str]
    has_bio: Optional[bool]
    date_added: Optional[str]
    detail_level: Optional[str]
    summary_fetched_at: Optional[str]
    full_fetched_at: Optional[str]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | sqlite3.Row) -> "MemorialRecord":
        """Create a record from private persistence values."""
        converted = dict(value)
        return cls(
            memorial_id=converted["memorial_id"],
            findagrave_url=converted.get("findagrave_url"),
            prefix=converted.get("prefix"),
            name=converted.get("name"),
            suffix=converted.get("suffix"),
            nickname=converted.get("nickname"),
            maiden_name=converted.get("maiden_name"),
            original_name=converted.get("original_name"),
            famous=(
                bool(converted["famous"])
                if converted.get("famous") is not None
                else None
            ),
            veteran=(
                bool(converted["veteran"])
                if converted.get("veteran") is not None
                else None
            ),
            birth=converted.get("birth"),
            birth_place=converted.get("birth_place"),
            death=converted.get("death"),
            death_place=converted.get("death_place"),
            memorial_type=converted.get("memorial_type"),
            cemetery_id=converted.get("cemetery_id"),
            burial_place=converted.get("burial_place"),
            plot=converted.get("plot"),
            coords=converted.get("coords"),
            has_bio=(
                bool(converted["has_bio"])
                if converted.get("has_bio") is not None
                else None
            ),
            date_added=converted.get("date_added"),
            detail_level=converted.get("detail_level"),
            summary_fetched_at=converted.get("summary_fetched_at"),
            full_fetched_at=converted.get("full_fetched_at"),
        )


@dataclass(frozen=True)
class CemeteryRecord:
    """Represent the current stored cemetery values associated with a memorial."""

    cemetery_id: int
    url: Optional[str]
    name: Optional[str]
    location: Optional[str]
    coords: Optional[str]
    first_observed_at: Optional[str]
    last_observed_at: Optional[str]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | sqlite3.Row) -> "CemeteryRecord":
        """Create a cemetery record from private persistence values."""
        converted = dict(value)
        return cls(
            cemetery_id=converted["cemetery_id"],
            url=converted.get("url"),
            name=converted.get("name"),
            location=converted.get("location"),
            coords=converted.get("coords"),
            first_observed_at=converted.get("first_observed_at"),
            last_observed_at=converted.get("last_observed_at"),
        )


@dataclass(frozen=True)
class MemorialRecordSnapshot:
    """Represent one successful saved provider response."""

    memorial_id: int
    findagrave_url: Optional[str]
    prefix: Optional[str]
    name: Optional[str]
    suffix: Optional[str]
    nickname: Optional[str]
    maiden_name: Optional[str]
    original_name: Optional[str]
    famous: Optional[bool]
    veteran: Optional[bool]
    birth: Optional[str]
    birth_place: Optional[str]
    death: Optional[str]
    death_place: Optional[str]
    memorial_type: Optional[str]
    cemetery_id: Optional[int]
    burial_place: Optional[str]
    plot: Optional[str]
    coords: Optional[str]
    has_bio: Optional[bool]
    date_added: Optional[str]
    displayed_relationships: tuple[DisplayedRelationshipInput, ...] = ()

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, Any] | sqlite3.Row
    ) -> "MemorialRecordSnapshot":
        """Create one snapshot from a saved success payload."""
        converted = dict(value)
        raw_relationships = converted.pop("findagrave_displayed_relationship_links", ())
        relationships = tuple(
            (
                item
                if isinstance(item, DisplayedRelationshipInput)
                else DisplayedRelationshipInput(**item)
            )
            for item in raw_relationships
        )
        return cls(
            memorial_id=converted["memorial_id"],
            findagrave_url=converted.get("findagrave_url"),
            prefix=converted.get("prefix"),
            name=converted.get("name"),
            suffix=converted.get("suffix"),
            nickname=converted.get("nickname"),
            maiden_name=converted.get("maiden_name"),
            original_name=converted.get("original_name"),
            famous=(
                bool(converted["famous"])
                if converted.get("famous") is not None
                else None
            ),
            veteran=(
                bool(converted["veteran"])
                if converted.get("veteran") is not None
                else None
            ),
            birth=converted.get("birth"),
            birth_place=converted.get("birth_place"),
            death=converted.get("death"),
            death_place=converted.get("death_place"),
            memorial_type=converted.get("memorial_type"),
            cemetery_id=converted.get("cemetery_id"),
            burial_place=converted.get("burial_place"),
            plot=converted.get("plot"),
            coords=converted.get("coords"),
            has_bio=(
                bool(converted["has_bio"])
                if converted.get("has_bio") is not None
                else None
            ),
            date_added=converted.get("date_added"),
            displayed_relationships=relationships,
        )


@dataclass(frozen=True)
class MemorialObservationRecord:
    """Represent one saved success or failure for a memorial request."""

    observation_id: int
    memorial_id: int
    cemetery_id: Optional[int]
    acquisition_level: str
    observed_at: str
    fetch_outcome: str
    parser_version: str
    snapshot: Optional[MemorialRecordSnapshot]
    attempted_url: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    target_url: Optional[str] = None
    target_memorial_id: Optional[int] = None

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, Any] | sqlite3.Row
    ) -> "MemorialObservationRecord":
        """Create one typed observation from a private database projection."""
        converted = dict(value)
        payload = json.loads(converted["payload_json"])
        snapshot = (
            MemorialRecordSnapshot.from_mapping(payload)
            if converted["fetch_outcome"] == "success"
            else None
        )
        return cls(
            observation_id=converted["observation_id"],
            memorial_id=converted["memorial_id"],
            cemetery_id=converted["cemetery_id"],
            acquisition_level=converted["acquisition_level"],
            observed_at=converted["observed_at"],
            fetch_outcome=converted["fetch_outcome"],
            parser_version=converted["parser_version"],
            snapshot=snapshot,
            attempted_url=payload.get("attempted_url"),
            error_type=payload.get("exception_type"),
            error_message=payload.get("error_message"),
            target_url=payload.get("target_url"),
            target_memorial_id=payload.get("target_memorial_id"),
        )


@dataclass(frozen=True)
class MemorialAliasRecord:
    """Represent current redirect resolution for one stored memorial."""

    requested_memorial_id: int
    canonical_memorial_id: int
    path: tuple[int, ...]
    is_active_source: bool
    canonical_target_exists: bool
    other_active_sources: tuple[int, ...]


@dataclass(frozen=True)
class MemorialRecordDetail:
    """Aggregate current values, saved versions and redirect information."""

    record: MemorialRecord
    cemetery: Optional[CemeteryRecord]
    observations: tuple[MemorialObservationRecord, ...]
    alias: MemorialAliasRecord


@dataclass(frozen=True)
class MemorialFetchRequest:
    """Request one immediate foreground retrieval by exact memorial identifier."""

    memorial_id: int

    def __post_init__(self) -> None:
        if self.memorial_id < 1:
            raise MemorialRecordInputError("Memorial ID must be positive")


@dataclass(frozen=True)
class MemorialFieldChange:
    """Describe a stored value changed by one full-record retrieval."""

    field: str
    previous: Optional[str | int | bool]
    current: Optional[str | int | bool]
    previous_observation_id: Optional[int]
    observation_id: int


@dataclass(frozen=True)
class MemorialFetchResult:
    """Describe one successfully saved foreground full-record retrieval."""

    memorial_id: int
    outcome: str
    full_observed_at: str
    previous_observation_id: Optional[int]
    observation_id: int
    changes: tuple[MemorialFieldChange, ...]
    unretained_values: tuple[MemorialFieldChange, ...]
    equal_fields: tuple[str, ...]
    displayed_relationship_links: int


class _MemorialRecordRepository:
    @staticmethod
    def list_records(
        connection: sqlite3.Connection, query: MemorialRecordQuery
    ) -> list[sqlite3.Row]:
        where = "WHERE g.cemetery_id = :cemetery_id" if query.cemetery_id else ""
        return connection.execute(
            f"""SELECT g.memorial_id, g.name, g.birth, g.death, g.cemetery_id,
                       g.burial_place, g.detail_level, g.findagrave_url,
                       COUNT(o.observation_id) AS saved_version_count,
                       MAX(o.observed_at) AS last_observed_at
                FROM graves AS g
                LEFT JOIN memorial_observations AS o
                  ON o.memorial_id = g.memorial_id
                {where}
                GROUP BY g.memorial_id
                ORDER BY COALESCE(g.name, '') COLLATE NOCASE, g.memorial_id
                LIMIT :limit""",
            {"cemetery_id": query.cemetery_id, "limit": query.limit},
        ).fetchall()

    @staticmethod
    def record(
        connection: sqlite3.Connection, memorial_id: int
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM graves WHERE memorial_id = ?", (memorial_id,)
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
               ORDER BY observed_at, observation_id""",
            (memorial_id,),
        ).fetchall()


def _memorial_id_from_url(url: str) -> Optional[int]:
    match = re.search(r"/memorial/(\d+)(?:/|$)", url)
    return int(match.group(1)) if match else None


@dataclass(frozen=True)
class MemorialRecordService:
    """Read stored memorials and perform exact immediate foreground retrievals."""

    database_name: str

    def list_records(
        self, query: MemorialRecordQuery = MemorialRecordQuery()
    ) -> tuple[MemorialRecordSummary, ...]:
        """Return stored memorials without requiring research tasks."""
        validate_current_database(self.database_name)
        with legacy_api._connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            rows = _MemorialRecordRepository.list_records(connection, query)
        return tuple(
            MemorialRecordSummary(
                memorial_id=row["memorial_id"],
                name=row["name"],
                birth=row["birth"],
                death=row["death"],
                cemetery_id=row["cemetery_id"],
                burial_place=row["burial_place"],
                detail_level=row["detail_level"],
                findagrave_url=row["findagrave_url"],
                saved_version_count=row["saved_version_count"],
                last_observed_at=row["last_observed_at"],
            )
            for row in rows
        )

    def get_record(self, memorial_id: int) -> MemorialRecordDetail:
        """Return one stored memorial and its saved versions without task state."""
        validate_current_database(self.database_name)
        with legacy_api._connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            record = _MemorialRecordRepository.record(connection, memorial_id)
            if record is None:
                raise MemorialRecordNotFound(memorial_id)
            cemetery = (
                _MemorialRecordRepository.cemetery(connection, record["cemetery_id"])
                if record["cemetery_id"] is not None
                else None
            )
            observations = _MemorialRecordRepository.observations(
                connection, memorial_id
            )
            resolution = legacy_api._resolve_alias(connection, memorial_id)
            canonical_id = resolution["canonical_memorial_id"]
            canonical_target_exists = (
                _MemorialRecordRepository.record(connection, canonical_id) is not None
            )
            other_sources = tuple(
                row[0]
                for row in connection.execute(
                    """SELECT source_memorial_id FROM memorial_aliases
                       WHERE target_memorial_id = ? AND status = 'active'
                         AND source_memorial_id != ?
                       ORDER BY source_memorial_id""",
                    (canonical_id, memorial_id),
                )
            )
        return MemorialRecordDetail(
            record=MemorialRecord.from_mapping(record),
            cemetery=(
                CemeteryRecord.from_mapping(cemetery) if cemetery is not None else None
            ),
            observations=tuple(
                MemorialObservationRecord.from_mapping(row) for row in observations
            ),
            alias=MemorialAliasRecord(
                requested_memorial_id=memorial_id,
                canonical_memorial_id=canonical_id,
                path=tuple(resolution["path"]),
                is_active_source=len(resolution["path"]) > 1,
                canonical_target_exists=canonical_target_exists,
                other_active_sources=other_sources,
            ),
        )

    def fetch(
        self,
        command: MemorialFetchRequest,
        *,
        acquire: Optional[
            Callable[[str], MemorialDetailInput | MemorialRedirectInput]
        ] = None,
        progress: Optional[ProgressObserver] = None,
        cancellation: Optional[CancellationToken] = None,
    ) -> MemorialFetchResult:
        """Retrieve and save one full record without changing research-task state."""
        operation = "fetch_memorial"
        token = cancellation or CancellationToken()
        token.raise_if_cancelled(operation, "validation")
        if progress is not None:
            progress(ProgressEvent(operation, "validation", 0, 1))
        current = self.get_record(command.memorial_id)
        if current.alias.is_active_source:
            raise MemorialFetchAliasBlocked(
                command.memorial_id,
                current.alias.canonical_memorial_id,
                current.alias.path,
            )
        attempted_url = current.record.findagrave_url or (
            MEMORIAL_CANONICAL_URL_FORMAT.format(command.memorial_id)
        )
        token.raise_if_cancelled(operation, "acquisition")
        if progress is not None:
            progress(ProgressEvent(operation, "acquisition", 0, 1))
        acquire_memorial: Callable[
            [str], MemorialDetailInput | MemorialRedirectInput | legacy_api.Memorial
        ]
        acquire_memorial = acquire or legacy_api.Memorial.parse
        try:
            acquired = acquire_memorial(attempted_url)
        except CancellationRequested:
            raise
        except legacy_api.MemorialMergedException as merged:
            source_id = _memorial_id_from_url(merged.old_url)
            target_id = _memorial_id_from_url(merged.new_url)
            if source_id != command.memorial_id or target_id is None:
                self._record_failure(command.memorial_id, attempted_url, merged)
                raise MemorialFetchRedirectInvalid(
                    command.memorial_id, merged
                ) from merged
            self._record_redirect_failure(
                command.memorial_id,
                target_id,
                merged.old_url,
                merged.new_url,
                merged,
            )
            raise MemorialFetchRedirected(command.memorial_id, target_id) from merged
        except Exception as error:
            self._record_failure(command.memorial_id, attempted_url, error)
            raise MemorialFetchFailed(command.memorial_id, error) from error
        if isinstance(acquired, MemorialRedirectInput):
            source_id = _memorial_id_from_url(acquired.source_url)
            target_id = _memorial_id_from_url(acquired.target_url)
            if source_id != command.memorial_id or target_id is None:
                invalid_redirect_error = ValueError(
                    "The adapter returned invalid redirect information"
                )
                self._record_failure(
                    command.memorial_id, attempted_url, invalid_redirect_error
                )
                raise MemorialFetchRedirectInvalid(
                    command.memorial_id, invalid_redirect_error
                )
            redirect_notice = RuntimeError(
                f"Memorial {command.memorial_id} redirects to {target_id}"
            )
            self._record_redirect_failure(
                command.memorial_id,
                target_id,
                acquired.source_url,
                acquired.target_url,
                redirect_notice,
            )
            raise MemorialFetchRedirected(command.memorial_id, target_id)
        memorial = (
            acquired._to_legacy()
            if isinstance(acquired, MemorialDetailInput)
            else acquired
        )
        if memorial.memorial_id != command.memorial_id:
            mismatch_error = ValueError(
                f"Requested memorial {command.memorial_id}, but acquired "
                f"{memorial.memorial_id}"
            )
            self._record_failure(command.memorial_id, attempted_url, mismatch_error)
            raise MemorialFetchInvalid(command.memorial_id, mismatch_error)
        token.raise_if_cancelled(operation, "persistence")
        if progress is not None:
            progress(ProgressEvent(operation, "persistence", 0, 1))
        memorial.save(database_name=self.database_name)
        completed = self.get_record(command.memorial_id)
        previous_observation_id = (
            current.observations[-1].observation_id if current.observations else None
        )
        latest = completed.observations[-1]
        changes = tuple(
            MemorialFieldChange(
                field,
                getattr(current.record, field),
                getattr(completed.record, field),
                previous_observation_id,
                latest.observation_id,
            )
            for field in _MEMORIAL_FIELDS
            if field != "memorial_id"
            and getattr(current.record, field) != getattr(completed.record, field)
        )
        retained = tuple(change for change in changes if change.current is not None)
        unretained = tuple(change for change in changes if change.current is None)
        equal_fields = tuple(
            field
            for field in _MEMORIAL_FIELDS
            if field != "memorial_id"
            and getattr(current.record, field) is not None
            and getattr(current.record, field) == getattr(completed.record, field)
        )
        relationship_count = (
            len(latest.snapshot.displayed_relationships)
            if latest.snapshot is not None
            else 0
        )
        result = MemorialFetchResult(
            memorial_id=command.memorial_id,
            outcome="saved",
            full_observed_at=latest.observed_at,
            previous_observation_id=previous_observation_id,
            observation_id=latest.observation_id,
            changes=retained,
            unretained_values=unretained,
            equal_fields=equal_fields,
            displayed_relationship_links=relationship_count,
        )
        if progress is not None:
            progress(ProgressEvent(operation, "completed", 1, 1))
        return result

    def _record_failure(
        self, memorial_id: int, attempted_url: str, error: Exception
    ) -> str:
        timestamp = legacy_api._utc_now_iso()
        error_message = " ".join(str(error).split())[:500]
        with legacy_api._connect(self.database_name) as connection:
            row = connection.execute(
                "SELECT cemetery_id FROM graves WHERE memorial_id = ?",
                (memorial_id,),
            ).fetchone()
            if row is None:
                raise MemorialRecordNotFound(memorial_id)
            connection.execute(
                """INSERT INTO memorial_observations (
                       memorial_id, cemetery_id, acquisition_level, observed_at,
                       fetch_outcome, parser_version, payload_json
                   ) VALUES (?, ?, 'full', ?, 'failure', ?, ?)""",
                (
                    memorial_id,
                    row[0],
                    timestamp,
                    legacy_api._package_version(),
                    json.dumps(
                        {
                            "attempted_url": attempted_url,
                            "exception_type": type(error).__name__,
                            "error_message": error_message,
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
        return timestamp

    def _record_redirect_failure(
        self,
        memorial_id: int,
        target_memorial_id: int,
        source_url: str,
        target_url: str,
        error: Exception,
    ) -> str:
        timestamp = legacy_api._utc_now_iso()
        error_message = " ".join(str(error).split())[:500]
        with legacy_api._connect(self.database_name) as connection:
            row = connection.execute(
                "SELECT cemetery_id FROM graves WHERE memorial_id = ?",
                (memorial_id,),
            ).fetchone()
            if row is None:
                raise MemorialRecordNotFound(memorial_id)
            legacy_api._record_alias(
                connection,
                memorial_id,
                target_memorial_id,
                "merged",
                source_url,
                target_url,
                None,
                timestamp,
                False,
            )
            connection.execute(
                """INSERT INTO memorial_observations (
                       memorial_id, cemetery_id, acquisition_level, observed_at,
                       fetch_outcome, parser_version, payload_json
                   ) VALUES (?, ?, 'full', ?, 'failure', ?, ?)""",
                (
                    memorial_id,
                    row[0],
                    timestamp,
                    legacy_api._package_version(),
                    json.dumps(
                        {
                            "attempted_url": source_url,
                            "exception_type": type(error).__name__,
                            "error_message": error_message,
                            "target_url": target_url,
                            "target_memorial_id": target_memorial_id,
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
        return timestamp
