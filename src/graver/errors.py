"""Stable, presentation-neutral application error contracts."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, ClassVar, Mapping, Optional

__all__ = (
    "ApplicationError",
    "DatabaseBusy",
    "DatabaseOperationError",
)


class ApplicationError(Exception):
    """Base class for supported failures returned to application clients.

    Attributes:
        code: Stable machine-readable classification suitable for adapter routing.
        summary: Safe, whitespace-normalized explanation for a human interface.
        context: Immutable structured values safe for logs and presentation.
    """

    code: ClassVar[str] = "application_error"

    def __init__(
        self, message: str, *, context: Optional[Mapping[str, Any]] = None
    ) -> None:
        self.summary = " ".join(str(message).split())
        self.context = MappingProxyType(dict(context or {}))
        super().__init__(self.summary)


class DatabaseOperationError(ApplicationError):
    """Report a database operation failure without exposing SQLite details."""

    code = "database_operation_failed"

    def __init__(self, database: str, operation: str):
        self.database = database
        self.operation = operation
        super().__init__(
            f"The database could not complete {operation}",
            context={"database": database, "operation": operation},
        )


class DatabaseBusy(DatabaseOperationError):
    """Report that another connection temporarily prevents a database operation."""

    code = "database_busy"

    def __init__(self, database: str, operation: str):
        self.database = database
        self.operation = operation
        ApplicationError.__init__(
            self,
            "The database is busy; retry after other work has finished",
            context={"database": database, "operation": operation},
        )
