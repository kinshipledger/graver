"""Typed researcher-directed acquisition services and receipts."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Callable, Optional

import graver.api as legacy_api
from graver.constants import CEMETERY_CANONICAL_URL_FORMAT
from graver.errors import ApplicationError
from graver.progress import (
    CancellationRequested,
    CancellationToken,
    ProgressEvent,
    ProgressObserver,
)
from graver.research import ResearchInputError
from graver.transport import TransportError

__all__ = (
    "AcquisitionFieldChange",
    "AcquisitionReceipt",
    "MemorialSearchFailed",
    "MemorialSummaryBatch",
    "MemorialSummaryInput",
    "MemorialSummarySearchRequest",
    "SummaryAcquisitionService",
)

_YEAR_FILTERS = ("", "exact", "before", "after", "1", "3", "5", "10", "25", "unknown")
_ORDERINGS = ("r", "n", "n-", "b", "b-", "d", "d-", "c", "c-", "dc", "dm", "pl")
_DATE_FILTERS = (1, 7, 30, 90, -90)
_PHOTO_FILTERS = (None, "photos", "nophotos")
_GPS_FILTERS = (None, "gps", "nogps")


class MemorialSearchFailed(ApplicationError):
    """Report a summary-search failure without exposing transport implementation."""

    code = "acquisition_failed"

    def __init__(self, cause: Exception):
        self.error_type = type(cause).__name__
        summary = (
            str(cause)
            if isinstance(cause, TransportError)
            else "The memorial summary search could not be completed"
        )
        super().__init__(
            summary,
            context={
                "operation": "search_memorial_summaries",
                "error_type": self.error_type,
            },
        )


@dataclass(frozen=True)
class MemorialSummarySearchRequest:
    """Describe one researcher-directed Find a Grave summary search.

    Fields use graver-style Python names even where the provider uses different
    parameter spelling. A zero ``max_results`` preserves the provider search's
    existing no-application-limit behavior; clients should normally choose a small
    explicit bound. Search criteria guide discovery and carry no evidentiary weight.
    """

    cemetery_id: Optional[int] = None
    firstname: str = ""
    middlename: str = ""
    lastname: str = ""
    fulltext: str = ""
    birth_year: Optional[int] = None
    birth_year_filter: str = ""
    death_year: Optional[int] = None
    death_year_filter: str = ""
    location: str = ""
    location_id: str = ""
    memorial_id: Optional[int] = None
    contributor_id: Optional[int] = None
    biography: str = ""
    linked_to_name: str = ""
    date_filter: Optional[int] = None
    order_by: str = "r"
    plot: str = ""
    no_cemetery: Optional[bool] = None
    famous: Optional[bool] = None
    sponsored: Optional[bool] = None
    cenotaph: Optional[bool] = None
    monument: Optional[bool] = None
    veteran: Optional[bool] = None
    tags: str = ""
    include_nickname: Optional[bool] = None
    include_maiden_name: Optional[bool] = None
    include_titles: Optional[bool] = None
    exact_name: Optional[bool] = None
    fuzzy_names: Optional[bool] = None
    photo_filter: Optional[str] = None
    gps_filter: Optional[str] = None
    flowers: Optional[bool] = None
    has_plot: Optional[bool] = None
    page: Optional[int] = None
    max_results: int = 0

    def __post_init__(self) -> None:
        if self.cemetery_id is not None and self.cemetery_id < 1:
            raise ResearchInputError("Cemetery ID must be positive")
        if self.memorial_id is not None and self.memorial_id < 1:
            raise ResearchInputError("Memorial ID must be positive")
        if self.contributor_id is not None and self.contributor_id < 1:
            raise ResearchInputError("Contributor ID must be positive")
        if self.page is not None and self.page < 1:
            raise ResearchInputError("Page must be positive")
        if self.max_results < 0:
            raise ResearchInputError("Maximum results cannot be negative")
        if self.birth_year_filter not in _YEAR_FILTERS:
            raise ResearchInputError("Unsupported birth-year filter")
        if self.death_year_filter not in _YEAR_FILTERS:
            raise ResearchInputError("Unsupported death-year filter")
        if self.order_by not in _ORDERINGS:
            raise ResearchInputError("Unsupported result ordering")
        if self.date_filter is not None and self.date_filter not in _DATE_FILTERS:
            raise ResearchInputError("Unsupported date-added filter")
        if self.photo_filter not in _PHOTO_FILTERS:
            raise ResearchInputError("Unsupported photo filter")
        if self.gps_filter not in _GPS_FILTERS:
            raise ResearchInputError("Unsupported GPS filter")
        if self.famous is not None and self.sponsored is not None:
            raise ResearchInputError(
                "Famous and sponsored filters are mutually exclusive"
            )
        if self.cenotaph is not None and self.monument is not None:
            raise ResearchInputError(
                "Cenotaph and monument filters are mutually exclusive"
            )
        if self.exact_name is not None and self.fuzzy_names is not None:
            raise ResearchInputError(
                "Exact-name and fuzzy-name filters are mutually exclusive"
            )


@dataclass(frozen=True)
class MemorialSummaryInput:
    """Carry one parsed memorial summary across the application boundary.

    Values are source observations, not accepted facts or identity conclusions.
    Missing values remain explicit rather than being inferred from other records.
    """

    memorial_id: int
    findagrave_url: str
    prefix: Optional[str]
    name: str
    suffix: Optional[str]
    nickname: Optional[str]
    maiden_name: Optional[str]
    famous: bool
    veteran: bool
    birth: Optional[str]
    death: Optional[str]
    memorial_type: Optional[str]
    cemetery_id: Optional[int]
    burial_place: Optional[str]
    plot: Optional[str]

    @classmethod
    def from_mapping(cls, values: dict) -> "MemorialSummaryInput":
        """Create a typed summary from parser-owned values."""
        return cls(**{name: values[name] for name in legacy_api.SUMMARY_FIELDS})

    def to_mapping(self) -> dict:
        """Return persistence values without exposing a database row."""
        return {name: getattr(self, name) for name in legacy_api.SUMMARY_FIELDS}


@dataclass(frozen=True)
class MemorialSummaryBatch:
    """Return captured summaries and their request source from an adapter.

    ``source`` identifies the request representation when the adapter can provide
    it. The batch owns no persistence behavior; graver validates and stores it.
    """

    memorials: tuple[MemorialSummaryInput, ...]
    source: Optional[str] = None


@dataclass(frozen=True)
class AcquisitionFieldChange:
    """Describe one current displayed value changed by a new observation.

    The change never implies that the new value is correct. Earlier immutable
    observations remain available even though the working display was updated.
    """

    memorial_id: int
    field: str
    previous: Optional[str | int | bool]
    current: Optional[str | int | bool]


@dataclass(frozen=True)
class AcquisitionReceipt:
    """Summarize persisted observations without exposing storage entities.

    ``memorials_created`` counts new local entities, while ``memorials_existing``
    counts known entities that received another dated observation. Every successful
    input appends one observation. ``changes`` explains only resulting differences
    in the current displayed representation; it does not replace snapshot history
    or make an evidentiary conclusion.
    """

    operation: str
    source: Optional[str]
    memorial_ids: tuple[int, ...]
    observations_appended: int
    memorials_created: int
    memorials_existing: int
    changed_memorials: int
    changes: tuple[AcquisitionFieldChange, ...]


@dataclass(frozen=True)
class _RetrievedSearch:
    batch: MemorialSummaryBatch
    cemetery: Optional[legacy_api.Cemetery] = None


def _provider_parameters(command: MemorialSummarySearchRequest) -> dict:
    parameters = {
        "max_results": command.max_results,
        "firstname": command.firstname,
        "middlename": command.middlename,
        "lastname": command.lastname,
        "fulltext": command.fulltext,
        "birthyear": str(command.birth_year) if command.birth_year is not None else "",
        "birthyearfilter": command.birth_year_filter,
        "deathyear": str(command.death_year) if command.death_year is not None else "",
        "deathyearfilter": command.death_year_filter,
        "location": command.location,
        "locationId": command.location_id,
        "memorialid": (
            str(command.memorial_id) if command.memorial_id is not None else ""
        ),
        "mcid": (
            str(command.contributor_id) if command.contributor_id is not None else ""
        ),
        "bio": command.biography,
        "linkedToName": command.linked_to_name,
        "datefilter": command.date_filter if command.date_filter is not None else "",
        "orderby": command.order_by,
        "plot": command.plot,
        "tags": command.tags,
    }
    optional = {
        "noCemetery": command.no_cemetery,
        "famous": command.famous,
        "sponsored": command.sponsored,
        "cenotaph": command.cenotaph,
        "monument": command.monument,
        "isVeteran": command.veteran,
        "includeNickName": command.include_nickname,
        "includeMaidenName": command.include_maiden_name,
        "includeTitles": command.include_titles,
        "exactName": command.exact_name,
        "fuzzyNames": command.fuzzy_names,
        "photofilter": command.photo_filter,
        "gpsfilter": command.gps_filter,
        "flowers": command.flowers,
        "hasPlot": command.has_plot,
        "page": command.page,
    }
    parameters.update(
        {name: value for name, value in optional.items() if value is not None}
    )
    return parameters


def _summary_input(value: object) -> MemorialSummaryInput:
    if isinstance(value, MemorialSummaryInput):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return MemorialSummaryInput.from_mapping(to_dict())
    raise TypeError("Acquisition adapters must return typed memorial summaries")


class SummaryAcquisitionService:
    """Coordinate one bounded summary search and atomic observation persistence."""

    def __init__(self, database_name: str):
        self.database_name = database_name

    def search(
        self,
        command: MemorialSummarySearchRequest,
        *,
        acquire: Optional[
            Callable[[MemorialSummarySearchRequest], MemorialSummaryBatch]
        ] = None,
        progress: Optional[ProgressObserver] = None,
        cancellation: Optional[CancellationToken] = None,
    ) -> AcquisitionReceipt:
        """Acquire summaries once and append their observations atomically."""
        operation = "search_memorial_summaries"
        token = cancellation or CancellationToken()
        token.raise_if_cancelled(operation, "validation")
        if progress is not None:
            progress(ProgressEvent(operation, "validation", 0, None))
        token.raise_if_cancelled(operation, "acquisition")
        if progress is not None:
            progress(ProgressEvent(operation, "acquisition", 0, None))
        try:
            retrieved = (
                _RetrievedSearch(self._normalize_batch(acquire(command)))
                if acquire is not None
                else self._retrieve(command)
            )
        except CancellationRequested:
            raise
        except Exception as error:
            raise MemorialSearchFailed(error) from error
        memorial_ids = tuple(item.memorial_id for item in retrieved.batch.memorials)
        if len(memorial_ids) != len(set(memorial_ids)):
            raise ResearchInputError("A summary search returned duplicate memorial IDs")
        token.raise_if_cancelled(operation, "persistence")
        if progress is not None:
            progress(ProgressEvent(operation, "persistence", 0, len(memorial_ids)))
        try:
            receipt = self._persist(retrieved)
        except sqlite3.Error:
            raise
        except Exception as error:
            raise MemorialSearchFailed(error) from error
        if progress is not None:
            progress(
                ProgressEvent(
                    operation, "completed", len(memorial_ids), len(memorial_ids)
                )
            )
        return receipt

    def _retrieve(self, command: MemorialSummarySearchRequest) -> _RetrievedSearch:
        cemetery = None
        if command.cemetery_id is not None:
            cemetery = legacy_api.Cemetery(
                CEMETERY_CANONICAL_URL_FORMAT.format(command.cemetery_id)
            )
        results = legacy_api.Memorial.search(cemetery, **_provider_parameters(command))
        source = getattr(results, "source", None)
        batch = MemorialSummaryBatch(
            tuple(_summary_input(result) for result in results), source=source
        )
        return _RetrievedSearch(batch, cemetery)

    @staticmethod
    def _normalize_batch(batch: MemorialSummaryBatch) -> MemorialSummaryBatch:
        return MemorialSummaryBatch(
            tuple(_summary_input(item) for item in batch.memorials), batch.source
        )

    def _persist(self, retrieved: _RetrievedSearch) -> AcquisitionReceipt:
        legacy_api._initialize_database(self.database_name)
        timestamp = legacy_api._utc_now_iso()
        created = 0
        changes: list[AcquisitionFieldChange] = []
        changed_ids: set[int] = set()
        with legacy_api._connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            if retrieved.cemetery is not None:
                self._persist_cemetery(connection, retrieved.cemetery, timestamp)
            for summary in retrieved.batch.memorials:
                before = connection.execute(
                    "SELECT * FROM graves WHERE memorial_id = ?", (summary.memorial_id,)
                ).fetchone()
                legacy_api._save_grave(
                    summary.to_mapping(),
                    legacy_api.SUMMARY_FIELDS,
                    "summary",
                    "summary_fetched_at",
                    database_name=self.database_name,
                    connection=connection,
                    timestamp=timestamp,
                )
                if before is None:
                    created += 1
                    continue
                after = connection.execute(
                    "SELECT * FROM graves WHERE memorial_id = ?", (summary.memorial_id,)
                ).fetchone()
                for field in legacy_api.SUMMARY_FIELDS:
                    if field == "memorial_id" or before[field] == after[field]:
                        continue
                    changes.append(
                        AcquisitionFieldChange(
                            summary.memorial_id, field, before[field], after[field]
                        )
                    )
                    changed_ids.add(summary.memorial_id)
        observed = len(retrieved.batch.memorials)
        return AcquisitionReceipt(
            operation="search_memorial_summaries",
            source=retrieved.batch.source,
            memorial_ids=tuple(item.memorial_id for item in retrieved.batch.memorials),
            observations_appended=observed,
            memorials_created=created,
            memorials_existing=observed - created,
            changed_memorials=len(changed_ids),
            changes=tuple(changes),
        )

    @staticmethod
    def _persist_cemetery(
        connection: sqlite3.Connection,
        cemetery: legacy_api.Cemetery,
        timestamp: str,
    ) -> None:
        connection.execute(
            """INSERT INTO cemeteries (
                   cemetery_id, url, name, location, coords,
                   first_observed_at, last_observed_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(cemetery_id) DO UPDATE SET
                   url = excluded.url,
                   name = excluded.name,
                   location = excluded.location,
                   coords = excluded.coords,
                   last_observed_at = excluded.last_observed_at""",
            (
                cemetery.cemetery_id,
                cemetery.findagrave_url,
                cemetery.name,
                cemetery.location,
                cemetery.coords,
                timestamp,
                timestamp,
            ),
        )
