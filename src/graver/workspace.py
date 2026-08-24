"""Synchronous typed workspace composition for non-CLI application clients."""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path

from graver.api import NotFound, ResearchTaskNotFound
from graver.database import (
    SchemaInspection,
    inspect_database,
    validate_current_database,
)
from graver.research import (
    ResearchQueueRequest,
    ResearchQueueResult,
    ResearchService,
    ResearchTaskDetail,
    ResearchTaskQuery,
    ResearchTaskRecord,
    ResearchTaskSummary,
    ResearchTaskUpdate,
)


class WorkItemNotFound(LookupError):
    """Report that no researcher-visible work item exists for a memorial."""

    def __init__(self, memorial_id: int):
        self.memorial_id = memorial_id
        super().__init__(f"Work item {memorial_id} does not exist")


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
        return self._service.query_tasks(query)

    def show(self, memorial_id: int) -> ResearchTaskDetail:
        """Return one task and its source context by researcher-facing memorial ID."""
        try:
            return self._service.get_task(memorial_id)
        except (NotFound, ResearchTaskNotFound) as error:
            raise WorkItemNotFound(memorial_id) from error

    def queue(self, command: ResearchQueueRequest) -> ResearchQueueResult:
        """Create research tasks idempotently for acquired memorials."""
        return self._service.queue_research(command)

    def update(self, command: ResearchTaskUpdate) -> ResearchTaskRecord:
        """Update one task only if its expected revision is still current."""
        try:
            return self._service.apply_task_update(command)
        except ResearchTaskNotFound as error:
            raise WorkItemNotFound(command.memorial_id) from error


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
