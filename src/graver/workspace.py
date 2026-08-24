"""Synchronous typed workspace composition for non-CLI application clients."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Callable, Optional

from graver.api import NotFound, ResearchTaskNotFound
from graver.database import (
    SchemaInspection,
    inspect_database,
    validate_current_database,
)
from graver.errors import ApplicationError, DatabaseBusy, DatabaseOperationError
from graver.progress import CancellationToken, ProgressObserver
from graver.research import (
    ResearchEnrichmentRequest,
    ResearchEnrichmentResult,
    ResearchQueueRequest,
    ResearchQueueResult,
    ResearchService,
    ResearchTaskDetail,
    ResearchTaskQuery,
    ResearchTaskRecord,
    ResearchTaskSummary,
    ResearchTaskUpdate,
)


class WorkItemNotFound(ApplicationError, LookupError):
    """Report that no researcher-visible work item exists for a memorial."""

    code = "resource_not_found"

    def __init__(self, memorial_id: int):
        self.memorial_id = memorial_id
        super().__init__(
            f"Work item {memorial_id} does not exist",
            context={"memorial_id": memorial_id},
        )


def _translate_database_error(
    error: sqlite3.Error, database: Path, operation: str
) -> ApplicationError:
    message = str(error).casefold()
    if "locked" in message or "busy" in message:
        return DatabaseBusy(str(database), operation)
    return DatabaseOperationError(str(database), operation)


@dataclass(frozen=True)
class WorkspaceDatabase:
    """Expose read-only lifecycle information for one explicit database path."""

    path: Path

    def inspect(self) -> SchemaInspection:
        """Inspect the workspace database without creating or migrating it."""
        return inspect_database(str(self.path))


@dataclass(frozen=True)
class WorkspaceWork:
    """Expose the typed research work queue without compatibility dictionaries."""

    _service: ResearchService

    def list(
        self, query: ResearchTaskQuery = ResearchTaskQuery()
    ) -> tuple[ResearchTaskSummary, ...]:
        """Return one deterministically ordered page of research work."""
        try:
            return self._service.query_tasks(query)
        except sqlite3.Error as error:
            raise _translate_database_error(
                error, Path(self._service.database_name), "list research work"
            ) from error

    def show(self, memorial_id: int) -> ResearchTaskDetail:
        """Return one task and its source context by researcher-facing memorial ID."""
        try:
            return self._service.get_task(memorial_id)
        except (NotFound, ResearchTaskNotFound) as error:
            raise WorkItemNotFound(memorial_id) from error
        except sqlite3.Error as error:
            raise _translate_database_error(
                error, Path(self._service.database_name), "show research work"
            ) from error

    def queue(self, command: ResearchQueueRequest) -> ResearchQueueResult:
        """Create research tasks idempotently for acquired memorials."""
        try:
            return self._service.queue_research(command)
        except sqlite3.Error as error:
            raise _translate_database_error(
                error, Path(self._service.database_name), "queue research work"
            ) from error

    def update(self, command: ResearchTaskUpdate) -> ResearchTaskRecord:
        """Update one task only if its expected revision is still current."""
        try:
            return self._service.apply_task_update(command)
        except ResearchTaskNotFound as error:
            raise WorkItemNotFound(command.memorial_id) from error
        except sqlite3.Error as error:
            raise _translate_database_error(
                error, Path(self._service.database_name), "update research work"
            ) from error


@dataclass(frozen=True)
class WorkspaceAcquisition:
    """Expose researcher-directed single-record acquisition to application clients."""

    _service: ResearchService

    def enrich(
        self,
        command: ResearchEnrichmentRequest,
        *,
        progress: Optional[ProgressObserver] = None,
        cancellation: Optional[CancellationToken] = None,
        acquire: Optional[Callable[[str], object]] = None,
    ) -> ResearchEnrichmentResult:
        """Retrieve and persist one approved memorial at safe cancellation boundaries."""
        try:
            return self._service.enrich_memorial(
                command,
                acquire=acquire,
                progress=progress,
                cancellation=cancellation,
            )
        except (NotFound, ResearchTaskNotFound) as error:
            raise WorkItemNotFound(command.memorial_id) from error
        except sqlite3.Error as error:
            raise _translate_database_error(
                error, Path(self._service.database_name), "enrich memorial"
            ) from error


@dataclass(frozen=True)
class GraverWorkspace:
    """Compose synchronous graver services around one validated database path.

    The workspace owns no long-lived SQLite connection and performs no CLI
    configuration lookup. Each operation opens and closes its own internal database
    unit of work.
    """

    path: Path

    @property
    def database(self) -> WorkspaceDatabase:
        """Return database lifecycle operations for this workspace."""
        return WorkspaceDatabase(self.path)

    @property
    def work(self) -> WorkspaceWork:
        """Return typed research work-queue operations for this workspace."""
        return WorkspaceWork(ResearchService(str(self.path)))

    @property
    def acquisition(self) -> WorkspaceAcquisition:
        """Return researcher-directed single-record acquisition operations."""
        return WorkspaceAcquisition(ResearchService(str(self.path)))


def open_workspace(database: str | PathLike[str]) -> GraverWorkspace:
    """Open a current database as a synchronous application workspace.

    Args:
        database: Explicit path to an existing current graver database.

    Returns:
        A lightweight workspace that owns no persistent database connection.

    Raises:
        DatabaseInspectionError: If the path is missing, unsafe, legacy, or invalid.
    """
    path = validate_current_database(str(database))
    return GraverWorkspace(path)
